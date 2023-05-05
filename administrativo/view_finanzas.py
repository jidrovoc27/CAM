import sys
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from datetime import *

from administrativo.forms import ConsultaForm, PagoForm, FacturaForm
from administrativo.funciones import add_data_aplication
from administrativo.models import *
from django.db.models import Sum
from django.template.loader import get_template


@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_finanzas(request):
    global ex
    data = {}
    add_data_aplication(request, data)
    usuario_logeado = request.user
    if Persona.objects.filter(usuario=usuario_logeado, status=True).exists():
        persona_logeado = Persona.objects.get(usuario=usuario_logeado, status=True)
    else:
        persona_logeado = 'CAM'
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']
            if peticion == 'pagar':
                try:
                    fechaactual = datetime.now().date()
                    idpersona = int(request.POST['id'])
                    personafactura = Persona.objects.get(id=idpersona)
                    rubros = request.POST.getlist('idrubro')
                    abonos = request.POST.getlist('abonorubro')
                    valortotal = 0
                    nuevasecuencia = generar_secuencial_factura()
                    numcompleto = '001-001-' + str(nuevasecuencia)
                    caja = Caja.objects.filter(status=True, persona=persona_logeado)
                    sesioncaja = None
                    if caja:
                        caja = caja.first()
                        sesioncaja = SesionCaja.objects.filter(status=True, caja=caja, inicio=fechaactual, fin=fechaactual, activo=True)
                        if sesioncaja:
                            sesioncaja = sesioncaja.first()
                    factura = Factura(persona_id=idpersona, fecha=datetime.now().date(), numero=nuevasecuencia,
                                      numerocompleto=numcompleto, sesioncaja=sesioncaja, identificacion=personafactura.cedula,
                                      tipo=1, nombre=personafactura.__str__(), email=personafactura.email, direccion=personafactura.direccion,
                                      telefono=personafactura.telefono_movil, electronica=True)
                    factura.save(request)

                    contador = 0
                    for rubrofact in rubros:
                        rubro = Rubro.objects.get(id=int(rubrofact))
                        abono = Pago(sesioncaja=sesioncaja, persona=personafactura, rubro=rubro, valor=Decimal(abonos[contador]),
                                     valorfinal=abonos[contador], fecha=fechaactual)
                        abono.save(request)
                        nuevodetalle = DetalleFactura(factura=factura, pago=abono)
                        nuevodetalle.save(request)
                        valorrecaudado  = ValorRecaudado(sesioncaja=sesioncaja,rubro=rubro, valor=Decimal(abonos[contador]))
                        valorrecaudado.save(request)
                        diferencial = solo_2_decimales(Decimal(rubro.saldo) - Decimal(abonos[contador]), 2)
                        rubro.saldo = diferencial
                        totalpagos = Pago.objects.filter(rubro=rubro, status=True).aggregate(total=Sum('valorfinal'))
                        if totalpagos['total']:
                            valorpagos = totalpagos['total']
                            if valorpagos == rubro.valor:
                                rubro.cancelado = True
                        rubro.save(request)
                        valortotal = valortotal + Decimal(abonos[contador])
                        contador += 1

                    factura.total = solo_2_decimales(valortotal, 2)
                    factura.save(request)

                    valida = conviert_html_to_pdf('factura.html', {'data': data})
                    if valida:
                        factura.archivo = f'facturas/{str(factura.id)}.pdf'
                        factura.save()

                    return redirect('/finanzas/?peticion=ver_rubro&id=%s' % request.POST['id'])

                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente mas tarde."})

            elif peticion == 'addfactura':
                try:
                    form = FacturaForm(request.POST,request.FILES)
                    archivo = None
                    if form.is_valid():
                        if 'archivo' in request.FILES:
                           archivo = request.FILES['archivo']
                        if not persona_logeado == 'AGENCIA':
                            registro_factura = Factura(pago_id=request.POST['idpago'],archivo=archivo,
                                                       persona=persona_logeado)
                            registro_factura.save(request)
                        else:
                            registro_factura = Factura(pago_id=request.POST['idpago'], archivo=archivo)
                            registro_factura.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Factura registrada correctamente."})
                except Exception as ex:
                    pass
        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'ver_rubro':
                try:
                    data['titulo'] = 'Rubros'
                    puedepagar = False
                    fechaactual = datetime.now().date()
                    if not persona_logeado == 'CAM':
                        cajadisponible = Caja.objects.filter(status=True, persona=persona_logeado, activo=True)
                        if cajadisponible:
                            sesioncajadisponible = SesionCaja.objects.filter(status=True, caja=cajadisponible.first(), activo=True, inicio=fechaactual)
                            if sesioncajadisponible:
                                puedepagar = True
                    data['persona'] = Persona.objects.get(id=request.GET['id'])
                    lista = Rubro.objects.filter(status=True, persona_id=request.GET['id'])
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['puedepagar'] = puedepagar
                    return render(request, "administrativo/finanzas/rubros.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            elif peticion == 'facturarcurso':
                try:
                    cursosporpagar = None
                    persona = Persona.objects.get(id=int(request.GET['id']))
                    alumno = Alumno.objects.filter(status=True, persona=persona)
                    if alumno:
                        cursosporpagar = Rubro.objects.filter(status=True, cancelado=False, persona=persona).values_list('curso_id', flat=True).order_by('curso_id').distinct('curso_id')
                        # data['cursosporpagar'] = cursosporpagar
                        data['cursosporpagar'] = Curso.objects.filter(status=True, id__in=cursosporpagar)
                        template = get_template("administrativo/finanzas/facturarcurso.html")
                        return JsonResponse({"respuesta": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            elif peticion == 'pagar':
                try:
                    id = request.GET['cursofacturar']
                    data['curso' ] = curso = Curso.objects.get(id=int(id))
                    data['persona'] = persona = Persona.objects.get(id=int(request.GET['id']))
                    data['rubrosopendientes'] = rubrosopendientes = Rubro.objects.filter(status=True, cancelado=False, curso=curso, persona=persona)
                    return render(request, "administrativo/finanzas/pagar.html", data)
                except Exception as ex:
                    pass

            elif peticion == 'ver_pagos':
                try:
                    data['titulo'] = 'Pagos'
                    data['persona_rubro'] = Persona.objects.get(id=request.GET['id'])
                    data['rubro_persona'] = Rubro.objects.get(status=True, id=request.GET['idrubro'])
                    lista = Pago.objects.filter(status=True, rubro_id=request.GET['idrubro'])
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    return render(request, "administrativo/finanzas/pagos.html", data)
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

            elif peticion == 'addpago':
                try:
                    data['titulo'] = 'Registrar nuevo pago'
                    data['titulo_formulario'] = 'Formulario de registro de pagos'
                    data['peticion'] = 'addpago'
                    data['idrubro'] = request.GET['idrubro']
                    data['id'] = request.GET['id']
                    form = PagoForm()
                    data['form'] = form
                    return render(request, "finanzas/addpago.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            elif peticion == 'addfactura':
                try:
                    data['titulo'] = 'Registrar nueva factura'
                    data['titulo_formulario'] = 'Formulario de registro de factura'
                    data['peticion'] = 'addfactura'
                    data['idpago'] = request.GET['idpago']
                    form = FacturaForm()
                    data['form'] = form
                    return render(request, "finanzas/addfactura.html", data)
                except Exception as ex:
                    pass

            elif peticion == 'ver_facturas':
                try:
                    data['titulo'] = 'Facturas'
                    data['paciente_rubro'] = Persona.objects.get(id=request.GET['paciente_id'])
                    data['pago_factura'] = Pago.objects.get(id=int(request.GET['id']))
                    lista = Factura.objects.filter(status=True,pago_id=int(request.GET['id']))
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    return render(request, "finanzas/facturas.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass


        else:
            try:
                data['titulo'] = 'Finanzas'
                data['titulo_tabla'] = 'Listado de personas'
                data['persona_logeado'] = persona_logeado
                lista = Persona.objects.filter(status=True)
                paginator = Paginator(lista, 15)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj

                return render(request, "administrativo/finanzas/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
