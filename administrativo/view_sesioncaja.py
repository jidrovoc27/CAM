import os
import sys
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import transaction
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from xhtml2pdf import pisa

from CAM import settings
from CAM.settings import BASE_DIR
from administrativo.forms import *
from administrativo.funciones import add_data_aplication
from administrativo.models import *

def create_mail(user_mail, subject, template_name, context):
    template = get_template(template_name)
    content = template.render(context)

    message = EmailMultiAlternatives(
        subject=subject,
        body='',
        from_email=settings.EMAIL_HOST_USER,
        to=[
            user_mail
        ],
        cc=[]
    )

    message.attach_alternative(content, 'text/html')
    return message
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    path_uri = str(BASE_DIR) + str(uri)
    result = finders.find(path_uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        sUrl = settings.STATIC_URL  # Typically /static/
        sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL  # Typically /media/
        mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path




def render_pdf_view(template_paths,data):
    template_path = template_paths
    context = data
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="factura.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_sesioncaja(request):
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

            if peticion == 'add_sesioncaja':
                try:
                    form = CajaForm(request.POST, request.FILES)
                    if form.is_valid():

                        campos_repetidos = list()

                        if Caja.objects.values('id').filter(nombre=form.cleaned_data['nombre'], persona=form.cleaned_data['encargado'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        descripcion = form.cleaned_data['descripcion']
                        activo = form.cleaned_data['activo']
                        persona = form.cleaned_data['encargado']

                        newcaja = Caja(persona=persona, nombre=nombre, descripcion=descripcion, activo=activo)
                        newcaja.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_sesioncaja':
                try:
                    form = CajaForm(request.POST, request.FILES)
                    if form.is_valid():

                        caja = Caja.objects.get(pk=request.POST['id'])
                        caja.nombre =request.POST['nombre']
                        caja.descripcion=request.POST['descripcion']
                        caja.persona_id=request.POST['encargado']
                        if 'activo' in request.POST:
                            caja.activo = True
                        else:
                            caja.activo = False
                        caja.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'eliminar_sesioncaja':
                try:
                    with transaction.atomic():
                        registro = SesionCaja.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

            if peticion == 'iniciarsesioncaja':
                try:
                    if not persona_logeado == 'CAM':
                        cajaasignada = Caja.objects.filter(status=True, persona=persona_logeado, activo=True)
                        if not cajaasignada:
                            return JsonResponse({"result": False, "mensaje": u"No tiene caja asignada"})

                        cajaasignada = cajaasignada.first()
                        if SesionCaja.objects.filter(caja=cajaasignada, inicio=datetime.now().date(), activo=True).exists():
                            return JsonResponse({"result": False, "mensaje": u"Ya existe sesión de caja abierta referente al día " + str(datetime.now().date())})

                        sesioncaja = SesionCaja(caja=cajaasignada,
                                                inicio=datetime.now().date(),
                                                fin=datetime.now().date(),
                                                valorinicial=0,
                                                activo=True)
                        sesioncaja.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"respuesta": False, "mensaje": "No tiene caja asignada"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})


            if peticion == 'cerrarsesioncaja':
                try:
                    if not persona_logeado == 'CAM':

                        sesioncaja = SesionCaja.objects.get(id=int(request.POST['id']))

                        totalfacturado = Pago.objects.filter(sesioncaja=sesioncaja, status=True).aggregate(total=Sum('valorfinal'))
                        totalfacturado = solo_2_decimales(Decimal(totalfacturado['total']), 2) if totalfacturado['total'] else 0

                        cierresesioncaja = CierreSesionCaja(sesioncaja=sesioncaja,
                                                fechacierre=datetime.now().date(),
                                                totalfacturado=totalfacturado)
                        cierresesioncaja.save(request)

                        sesioncaja.activo = False
                        sesioncaja.fin = datetime.now().date()
                        sesioncaja.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Sesión cerrada correctamente."})
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"respuesta": False, "mensaje": "No tiene caja asignada"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_sesioncaja':
                try:
                    data['titulo'] = 'Agregar nueva caja'
                    data['titulo_formulario'] = 'Formulario de registro de cajas'
                    data['peticion'] = 'add_sesioncaja'
                    form = CajaForm()
                    data['form'] = form
                    return render(request, "administrativo/caja/add_caja.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'edit_sesioncaja':
                try:
                    data['titulo'] = 'Editar sesión caja'
                    data['titulo_formulario'] = 'Edición de sesión caja'
                    data['peticion'] = 'edit_sesioncaja'
                    data['caja'] = caja = Caja.objects.get(pk=request.GET['id'])
                    form = CajaForm(initial={
                        'nombre':caja.nombre,
                        'descripcion': caja.descripcion,
                        'encargado': caja.persona,
                        'activo': caja.activo})
                    data['form'] = form
                    return render(request, "administrativo/caja/edit_caja.html", data)
                except Exception as ex:
                    pass

        else:
            try:
                data['titulo'] = 'Sesiones de caja'
                data['titulo_tabla'] = 'Lista  de sesiones de caja'
                data['persona_logeado'] = persona_logeado
                lista = SesionCaja.objects.filter(status=True).order_by('id')
                paginator = Paginator(lista, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/sesioncaja/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
