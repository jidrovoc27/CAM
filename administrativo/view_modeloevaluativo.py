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

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_modeloevaluativo(request):
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

            if peticion == 'add_modeloevaluativo':
                try:
                    form = ModeloEvaluativoForm(request.POST)
                    if form.is_valid():

                        campos_repetidos = list()

                        if ModeloEvaluativo.objects.values('id').filter(nombre=form.cleaned_data['nombre'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        notamaxima = form.cleaned_data['notamaxima']
                        notaaprobar = form.cleaned_data['notaaprobar']
                        asistenciaaprobar = form.cleaned_data['asistenciaaprobar']
                        observaciones = form.cleaned_data['observaciones']

                        newmodelo = ModeloEvaluativo(nombre=nombre, fecha=datetime.now().date(), notamaxima=notamaxima,
                                                     notaaprobar=notaaprobar, asistenciaaprobar=asistenciaaprobar,
                                                     observaciones=observaciones)
                        newmodelo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_modeloevaluativo':
                try:
                    form = ModeloEvaluativoForm(request.POST)
                    if form.is_valid():

                        campos_repetidos = list()

                        if ModeloEvaluativo.objects.values('id').filter(nombre=form.cleaned_data['nombre'], status=True).exclude(id=int(request.POST['id'])).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        notamaxima = form.cleaned_data['notamaxima']
                        notaaprobar = form.cleaned_data['notaaprobar']
                        asistenciaaprobar = form.cleaned_data['asistenciaaprobar']
                        observaciones = form.cleaned_data['observaciones']

                        newmodelo = ModeloEvaluativo.objects.get(id=int(request.POST['id']))
                        newmodelo.nombre = nombre
                        newmodelo.notamaxima = notamaxima
                        newmodelo.notaaprobar = notaaprobar
                        newmodelo.asistenciaaprobar = asistenciaaprobar
                        newmodelo.observaciones = observaciones
                        newmodelo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_detallemodeloevaluativo':
                try:
                    form = DetalleModeloEvaluativoForm(request.POST)
                    if form.is_valid():

                        campos_repetidos = list()

                        if DetalleModeloEvaluativo.objects.values('id').filter(modelo_id=int(request.POST['modelo']), nombre=form.cleaned_data['nombre'], status=True).exclude(id=int(request.POST['id'])).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        notamaxima = form.cleaned_data['notamaxima']
                        notaminima = form.cleaned_data['notaminima']
                        orden = form.cleaned_data['orden']

                        actdetallemodelo = DetalleModeloEvaluativo.objects.get(id=int(request.POST['id']))
                        actdetallemodelo.nombre = nombre
                        actdetallemodelo.notamaxima = notamaxima
                        actdetallemodelo.notaminima = notaminima
                        actdetallemodelo.orden = orden
                        actdetallemodelo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'add_detallemodeloevaluativo':
                try:
                    form = DetalleModeloEvaluativoForm(request.POST)
                    if form.is_valid():

                        campos_repetidos = list()

                        if DetalleModeloEvaluativo.objects.values('id').filter(modelo_id=int(request.POST['id']), nombre=form.cleaned_data['nombre'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        notaminima = form.cleaned_data['notaminima']
                        notamaxima = form.cleaned_data['notamaxima']
                        orden = form.cleaned_data['orden']

                        newdetallemodelo = DetalleModeloEvaluativo(modelo_id=int(request.POST['id']), nombre=nombre, notaminima=notaminima, notamaxima=notamaxima,
                                                     orden=orden)
                        newdetallemodelo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'finalizar_modelo':
                try:
                    id = int(request.POST['id'])
                    modelo = ModeloEvaluativo.objects.get(id=id)
                    if DetalleModeloEvaluativo.objects.filter(status=True, modelo=modelo).exists():
                        modelo.finalizado = True
                        modelo.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Modelo finalizado correctamente"})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": "El modelo evaluativo debe de contar con detalles calificativos."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_caja':
                try:
                    form = ModeloEvaluativoForm(request.POST)
                    if form.is_valid():

                        modelo = ModeloEvaluativo.objects.get(pk=request.POST['id'])
                        modelo.nombre =request.POST['nombre']
                        modelo.notamaxima =request.POST['notamaxima']
                        modelo.notaaprobar =request.POST['notaaprobar']
                        modelo.asistenciaaprobar =request.POST['asistenciaaprobar']
                        modelo.observaciones=request.POST['observaciones']
                        modelo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'eliminar_modelo':
                try:
                    with transaction.atomic():
                        registro = ModeloEvaluativo.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})
                except Exception as ex:
                    pass

            if peticion == 'eliminar_detallemodelo':
                try:
                    with transaction.atomic():
                        registro = DetalleModeloEvaluativo.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})
                except Exception as ex:
                    pass

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_modeloevaluativo':
                try:
                    data['titulo'] = 'Agregar nuevo modelo evaluativo'
                    data['titulo_formulario'] = 'Formulario de registro de modelo evaluativo'
                    data['peticion'] = 'add_modeloevaluativo'
                    form = ModeloEvaluativoForm()
                    data['form'] = form
                    return render(request, "administrativo/modeloevaluativo/add_modeloevaluativo.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'add_detallemodeloevaluativo':
                try:
                    data['titulo'] = 'Agregar nuevo detalle al modelo evaluativo'
                    data['titulo_formulario'] = 'Formulario de registro de detalle al modelo evaluativo'
                    data['peticion'] = 'add_detallemodeloevaluativo'
                    data['modelo'] = ModeloEvaluativo.objects.get(id=int(request.GET['id']))
                    form = DetalleModeloEvaluativoForm()
                    data['form'] = form
                    return render(request, "administrativo/modeloevaluativo/add_detallemodeloevaluativo.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'edit_detallemodeloevaluativo':
                try:
                    data['titulo'] = 'Editar detalle modelo evaluativo'
                    data['titulo_formulario'] = 'Edición de detalle modelo evaluativo'
                    data['peticion'] = 'edit_detallemodeloevaluativo'
                    data['modelo'] = modelo = ModeloEvaluativo.objects.get(pk=request.GET['modelo'])
                    data['detalle'] = detalle = DetalleModeloEvaluativo.objects.get(id=request.GET['id'])
                    form = DetalleModeloEvaluativoForm(initial={
                        'nombre':detalle.nombre,
                        'notaminima': detalle.notaminima,
                        'notamaxima': detalle.notamaxima,
                        'orden': detalle.orden,}
                    )
                    data['form'] = form
                    return render(request, "administrativo/modeloevaluativo/edit_detallemodeloevaluativo.html", data)
                except Exception as ex:
                    pass

            if peticion == 'edit_modeloevaluativo':
                try:
                    data['titulo'] = 'Editar modelo evaluativo'
                    data['titulo_formulario'] = 'Edición de modelo evaluativo'
                    data['peticion'] = 'edit_modeloevaluativo'
                    data['modelo'] = modelo = ModeloEvaluativo.objects.get(pk=request.GET['id'])
                    form = ModeloEvaluativoForm(initial={
                        'nombre':modelo.nombre,
                        'notamaxima': modelo.notamaxima,
                        'notaaprobar': modelo.notaaprobar,
                        'asistenciaaprobar': modelo.asistenciaaprobar,
                        'observaciones': modelo.observaciones,}
                    )
                    data['form'] = form
                    return render(request, "administrativo/modeloevaluativo/edit_modeloevaluativo.html", data)
                except Exception as ex:
                    pass

            if peticion == 'detallemodelo':
                try:
                    data['titulo'] = 'Detalle del modelo evaluativo'
                    data['titulo_tabla'] = 'Detalle del modelo evaluativo'
                    data['modelo'] = modelo = ModeloEvaluativo.objects.get(id=int(request.GET['id']))
                    data['persona_logeado'] = persona_logeado
                    lista = DetalleModeloEvaluativo.objects.filter(status=True, modelo=modelo)
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    return render(request, "administrativo/modeloevaluativo/detallemodelo.html", data)
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

        else:
            try:
                data['titulo'] = 'Modelos evaluativos'
                data['titulo_tabla'] = 'Lista  de modelos evaluativo'
                data['persona_logeado'] = persona_logeado
                lista = ModeloEvaluativo.objects.filter(status=True).order_by('id')
                paginator = Paginator(lista, 15)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/modeloevaluativo/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
