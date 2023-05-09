import os
import sys
from io import StringIO
import datetime
from datetime import *
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
def view_tiporubro(request):
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

            if peticion == 'add_tiporubro':
                try:
                    form = TipoRubroForm(request.POST)
                    if form.is_valid():

                        campos_repetidos = list()

                        if TipoOtroRubro.objects.values('id').filter(nombre=form.cleaned_data['nombre'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "registro ya existe.", 'repetidos': campos_repetidos})

                        nombre = form.cleaned_data['nombre']
                        descripcion = form.cleaned_data['descripcion']

                        tiporubro = TipoOtroRubro(
                            nombre=nombre,
                            descripcion=descripcion)
                        tiporubro.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_tiporubro':
                try:
                    form = TipoRubroForm(request.POST)
                    if form.is_valid():
                        tiporubro = TipoOtroRubro.objects.get(pk=request.POST['id'])
                        tiporubro.nombre = request.POST['nombre']
                        tiporubro.descripcion = request.POST['descripcion']
                        tiporubro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})
                except Exception as ex:
                    pass

            if peticion == 'eliminar_tiporubro':
                try:
                    with transaction.atomic():
                        registro = TipoOtroRubro.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_tiporubro':
                try:
                    data['titulo'] = 'Agregar nuevo tipo rubro'
                    data['titulo_formulario'] = 'Formulario de registro de tipos rubro'
                    data['peticion'] = 'add_tiporubro'
                    form = TipoRubroForm()
                    data['form'] = form
                    return render(request, "administrativo/tiporubro/add_tiporubro.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'historial_clinico':
                try:
                    data['titulo'] = 'Historial clínico'
                    data['paciente_id'] = paciente_id = request.GET['id']
                    data['datos_docente'] = Docente.objects.get(id=paciente_id)
                    return render(request, "docente/menu_historial_clinico/datos_docente.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'submenu_documentos':
                try:
                    data['titulo'] = 'Documentos'
                    data['titulo_tabla'] = 'Documentos'
                    data['paciente_id'] = paciente_id = request.GET['id']
                    lista = Documentos.objects.filter(paciente_id=paciente_id, status=True)
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    return render(request, "docente/menu_historial_clinico/documentos.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'add_documento':
                try:
                    form = DocumentoForm()
                    data['paciente_id'] = paciente_id = int(request.GET['paciente_id'])
                    data['form'] = form
                    data['peticion'] = 'add_documento'
                    template = get_template('docente/menu_historial_clinico/modal/formadddocumento.html')
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            if peticion == 'edit_tiporubro':
                try:
                    data['titulo'] = 'Editar tipo rubro'
                    data['titulo_formulario'] = 'Edición de tipo rubro'
                    data['peticion'] = 'edit_tiporubro'
                    data['tiporubro'] = tiporubro = TipoOtroRubro.objects.get(pk=request.GET['id'])
                    form = TipoRubroForm(initial={
                        'nombre':tiporubro.nombre,
                        'descripcion': tiporubro.descripcion})
                    data['form'] = form
                    return render(request, "administrativo/tiporubro/edit_tiporubro.html", data)
                except Exception as ex:
                    pass

            if peticion == 'enviar_correo':
                try:
                    from django.conf import settings
                    from django.core.mail import send_mail

                    send_mail(
                        'Título del correo',
                        'Hola, este correo es enviado desde un post en PyWombat. 🐍',
                        settings.EMAIL_HOST_USER,
                        ['nelson-emelec@live.com'],
                        fail_silently=False
                    )
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

            if peticion == 'validar_cedula':
                cedula = request.GET['cedula']
                persona = Persona.objects.filter(status=True, cedula=cedula)
                if persona.exists():
                    return JsonResponse({"respuesta": True, 'mensaje': 'Cédula ya existe'})
                else:
                    return JsonResponse({"respuesta": False, 'mensaje': ''})

            if peticion == 'validar_usuario':
                usuario = request.GET['usuario']
                persona = User.objects.filter(username=usuario)
                if persona.exists():
                    return JsonResponse({"respuesta": True, 'mensaje': 'Usuario ya existe'})
                else:
                    return JsonResponse({"respuesta": False, 'mensaje': ''})

            if peticion == 'validar_email':
                correo = request.GET['email']
                email = Persona.objects.filter(email=correo, status=True)
                if email.exists():
                    return JsonResponse({"respuesta": True, 'mensaje': 'Email ya existe'})
                else:
                    return JsonResponse({"respuesta": False, 'mensaje': ''})


        else:
            try:
                data['titulo'] = 'Tipo rubros'
                data['titulo_tabla'] = 'Lista  de tipo de rubros'
                data['persona_logeado'] = persona_logeado
                lista = TipoOtroRubro.objects.filter(status=True).order_by('id')
                paginator = Paginator(lista, 15)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/tiporubro/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
