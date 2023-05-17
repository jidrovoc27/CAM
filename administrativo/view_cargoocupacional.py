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
from django.db.models import Q



@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_cargoocupacional(request):
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

            if peticion == 'add_cargo':
                try:
                    form = CargoForm(request.POST, request.FILES)
                    if form.is_valid():

                        campos_repetidos = list()

                        if Cargo.objects.values('id').filter(nombre=form.cleaned_data['nombre'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']

                        newcargo = Cargo(nombre=nombre)
                        newcargo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_cargo':
                try:
                    form = CargoForm(request.POST)
                    if form.is_valid():

                        cargo = Cargo.objects.get(pk=request.POST['id'])
                        cargo.nombre =request.POST['nombre']
                        cargo.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'eliminar_cargo':
                try:
                    with transaction.atomic():
                        registro = Cargo.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_cargo':
                try:
                    data['titulo'] = 'Agregar nuevo cargo'
                    data['titulo_formulario'] = 'Formulario de registro de cargos'
                    data['peticion'] = 'add_cargo'
                    form = CargoForm()
                    data['form'] = form
                    return render(request, "administrativo/cargos/add_cargo.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'edit_cargo':
                try:
                    data['titulo'] = 'Editar cargo'
                    data['titulo_formulario'] = 'Edición de cargo'
                    data['peticion'] = 'edit_cargo'
                    data['cargo'] = cargo = Cargo.objects.get(pk=request.GET['id'])
                    form = CargoForm(initial={
                        'nombre':cargo.nombre})
                    data['form'] = form
                    return render(request, "administrativo/cargos/edit_cargo.html", data)
                except Exception as ex:
                    pass

        else:
            try:
                data['titulo'] = 'Cargos ocupacionales'
                data['titulo_tabla'] = 'Lista  de cargos'
                data['persona_logeado'] = persona_logeado
                filtro = (Q(status=True))
                ruta_paginado = request.path
                if 'var' in request.GET:
                    var = request.GET['var']
                    data['var'] = var
                    filtro = filtro & (Q(nombre__icontains=var))
                    ruta_paginado += "?var=" + var + "&"
                lista = Cargo.objects.filter(filtro).order_by('id')
                paginator = Paginator(lista, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/cargos/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
