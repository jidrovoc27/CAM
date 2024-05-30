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
from administrativo.forms import PersonaForm, AbonarCuotaForm, DocumentoForm
from administrativo.funciones import add_data_aplication
from administrativo.models import *
from chat.models import *
from django.db.models import Q

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_alumno(request):
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

            if peticion == 'add_alumno':
                try:
                    form = PersonaForm(request.POST, request.FILES)
                    if form.is_valid():

                        campos_repetidos = list()

                        if Persona.objects.values('id').filter(cedula=form.cleaned_data['cedula'], status=True).exists():
                            campos_repetidos.append(form['cedula'].name)
                        if Persona.objects.values('id').filter(email=form.cleaned_data['email'], status=True).exists():
                            campos_repetidos.append(form['email'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "registro ya existe.", 'repetidos': campos_repetidos})
                        username = form.cleaned_data['nombres']
                        password = form.cleaned_data['cedula'].replace(' ','')
                        nombres = form.cleaned_data['nombres']
                        # nombre2 = form.cleaned_data['nombre2']
                        apellidos = form.cleaned_data['apellidos']
                        # apellido2 = form.cleaned_data['apellido2']
                        cedula = form.cleaned_data['cedula']
                        genero = form.cleaned_data['genero']
                        ciudad = form.cleaned_data['ciudad']
                        direccion = form.cleaned_data['direccion']
                        referencia = form.cleaned_data['referencia']
                        telefono_movil = form.cleaned_data['telefono_movil']
                        telefono_convencional = form.cleaned_data['telefono_convencional']
                        email = form.cleaned_data['email']
                        username = form.cleaned_data['nombres'].replace(' ','').lower()  # Eliminar espacios y líneas nuevas
                        password = password.lower()
                        usuario = User.objects.create_user(username, email, password)
                        usuario.save()

                        grupo = Group.objects.get(name='Alumno')  # ALUMNO
                        grupo.user_set.add(usuario)

                        persona = Persona(
                            usuario=usuario,
                            nombres=nombres,
                            # nombre2=nombre2,
                            apellidos=apellidos,
                            # apellido2=apellido2,
                            email=email,
                            cedula=cedula,
                            genero=genero,
                            telefono_movil=telefono_movil,
                            telefono_convencional=telefono_convencional,
                            ciudad=ciudad,
                            direccion=direccion,
                            referencia=referencia
                        )
                        persona.save(request)
                        if 'foto' in request.FILES:
                            foto = request.FILES['foto']
                            persona.foto = foto
                            persona.save(request)
                            existe = Profile.objects.filter(user_id=persona.usuario.id)
                            if existe.exists():
                                existe.update(pic=persona.foto)

                        persona_perfil = PersonaPerfil(
                            persona=persona,
                            is_alumno=True
                        )

                        persona_perfil.save(request)

                        newalumno = Alumno(
                            persona=persona
                        )
                        newalumno.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_alumno':
                try:
                    form = PersonaForm(request.POST, request.FILES)
                    if form.is_valid():
                        paciente = Alumno.objects.get(pk=request.POST['id'])
                        persona = Persona.objects.get(pk = paciente.persona_id)
                        persona.nombres =request.POST['nombres']
                        persona.apellidos=request.POST['apellidos']
                        persona.email=request.POST['email']
                        persona.cedula=request.POST['cedula']
                        persona.genero_id=request.POST['genero']
                        persona.ciudad=request.POST['ciudad']
                        persona.direccion=request.POST['direccion']
                        persona.referencia=request.POST['referencia']
                        persona.telefono_movil=request.POST['telefono_movil']
                        persona.telefono_convencional=request.POST['telefono_convencional']
                        persona.save(request)
                        if 'foto' in request.FILES:
                            foto = form.cleaned_data['foto']
                            persona.foto = foto
                            persona.save(request)
                            existe = Profile.objects.filter(user_id=persona.usuario.id)
                            if existe:
                                existe.update(pic=persona.foto)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro Modificado correctamente."})


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'eliminar_alumno':
                try:
                    with transaction.atomic():
                        registro = Alumno.objects.get(pk=request.POST['id'])
                        persona = Persona.objects.get(pk=registro.persona_id)
                        persona.status = False
                        persona.save()
                        registro.status = False
                        registro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

            if peticion == 'resetear_clave':
                try:
                    with transaction.atomic():
                        persona = Persona.objects.get(pk=request.POST['id'])
                        persona.usuario.set_password(str(persona.cedula))
                        persona.usuario.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Clave reseteada correctamente"})

                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'add_documento':
                try:
                    form = DocumentoForm(request.POST, request.FILES)
                    archivo = None
                    if form.is_valid():
                        if 'archivo' in request.FILES:
                            archivo = request.FILES['archivo']
                        registrodocumento = Documentos(nombre=form.cleaned_data['nombre'],
                                                       archivo=archivo,
                                                       paciente_id=int(request.POST['id']))
                        registrodocumento.save()
                    return redirect('/pacientes/?peticion=submenu_documentos&id=%s' % request.POST['id'])
                except Exception as ex:
                    pass
        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_alumno':
                try:
                    data['titulo'] = 'Agregar nuevo alumno'
                    data['titulo_formulario'] = 'Formulario de registro de alumnos'
                    data['peticion'] = 'add_alumno'
                    form = PersonaForm()
                    data['form'] = form
                    return render(request, "administrativo/alumno/add_alumno.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'historial_clinico':
                try:
                    data['titulo'] = 'Historial clínico'
                    data['paciente_id'] = paciente_id = request.GET['id']
                    data['datos_docente'] = Alumno.objects.get(id=paciente_id)
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
                    paginator = Paginator(lista, 25)
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

            if peticion == 'edit_alumno':
                try:
                    data['titulo'] = 'Editar cliente'
                    data['titulo_formulario'] = 'Edición de cliente'
                    data['peticion'] = 'edit_alumno'
                    data['alumno'] = alumno = Alumno.objects.get(pk=request.GET['id'])
                    form = PersonaForm(initial={
                        'nombres':alumno.persona.nombres,
                        'apellidos': alumno.persona.apellidos,
                        'email': alumno.persona.email,
                        'cedula': alumno.persona.cedula,
                        'genero': alumno.persona.genero,
                        'ciudad':alumno.persona.ciudad,
                        'direccion':alumno.persona.direccion,
                        'referencia':alumno.persona.referencia,
                        'telefono_movil': alumno.persona.telefono_movil,
                        'telefono_convencional': alumno.persona.telefono_convencional,
                        'foto': alumno.persona.foto
                    })
                    form.editar()
                    data['form'] = form
                    return render(request, "administrativo/alumno/edit_alumno.html", data)
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
                data['titulo'] = 'Alumnos'
                data['titulo_tabla'] = 'Lista  de Alumnos'
                data['persona_logeado'] = persona_logeado
                filtro = (Q(status=True))
                ruta_paginado = request.path
                if 'var' in request.GET:
                    var = request.GET['var']
                    data['var'] = var
                    filtro = filtro & (Q(persona__nombres__icontains=var) |
                                       Q(persona__apellidos__icontains=var) |
                                       Q(persona__cedula__icontains=var))
                    ruta_paginado += "?var=" + var + "&"
                lista = Alumno.objects.filter(filtro).order_by('id')
                paginator = Paginator(lista, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/alumno/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
