import sys

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import PasswordChangeView
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from administrativo.models import *
from administrativo.funciones import *
from administrativo.forms import *
from CAM import settings
from django.db.models import Q, F, Count
from CAM.settings import *


# Create your views here.
from django.urls import reverse_lazy

# Create your views here.

@transaction.atomic()
def login_usuario(request):
    global ex
    data = {}
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']
            if peticion == 'login_usuario':
                try:
                    usuario = authenticate(username=request.POST['usuario'].lower().strip(), password=request.POST['clave'])
                    if usuario is not None:
                        if usuario.is_active:
                            persona_logeado = Persona.objects.filter(usuario=usuario, status=True)
                            if persona_logeado:
                                persona_logeado = persona_logeado.first()
                                if not persona_logeado == 'CAM':
                                    mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
                                    if mis_perfiles:
                                        mis_perfiles = mis_perfiles.first()
                                        if not mis_perfiles.is_administrador or not mis_perfiles.is_profesor:
                                            return JsonResponse({"respuesta": False, 'mensaje': u'No tiene perfil administrativo o docente'})
                            login(request, usuario)
                            return JsonResponse({"respuesta": True, "url": settings.LOGIN_REDIRECT_URL})
                        else:
                            return JsonResponse({"respuesta": False, 'mensaje': u'Inicio de sesión incorrecto, usuario no activo.'})
                    else:
                        return JsonResponse({"respuesta": False,'mensaje': u'Inicio de sesión incorrecto, usuario o clave no coinciden.'})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse(
                        {"respuesta": False, "mensaje": "Error al iniciar sesión, intentelo más tarde."})
        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
        else:
            try:
                if 'persona' in request.session:
                    return HttpResponseRedirect("/")
                data['titulo'] = 'Inicio de sesión'
                data['request'] = request
                return render(request, "registration/login.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))


def paginaweb(request):
    data = {}
    fechaactual = datetime.now().date()
    filtro = (Q(status=True) & Q(finalizarcurso=False))
    data['cursosofertados'] = cursosofertados = Curso.objects.filter(filtro).filter(status=True, periodo__status=True, oferta=True)
    data['cursosdisponibles'] = Curso.objects.filter(filtro).filter(status=True, periodo__status=True, fechainicio__lte=fechaactual, fechafin__gte=fechaactual)
    data['cursosproximos'] = Curso.objects.filter(filtro).filter(status=True, periodo__status=True, fechainicio__gte=fechaactual)
    data['docentes'] = Docente.objects.filter(status=True)
    return render(request, "baseweb.html", data)

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def dashboard(request):
    global ex
    data = {}
    add_data_aplication(request, data)
    usuario_logeado = request.user
    if 'tipoperfil' in request.session:
        tipoperfil = request.session['tipoperfil']
    else:
        tipoperfil = usuario_logeado.groups.all()
    if  Persona.objects.filter(usuario=usuario_logeado, status=True).exists():
        persona_logeado = Persona.objects.get(usuario=usuario_logeado, status=True)
    else:
        persona_logeado = 'CAM'

    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']

            if peticion == 'cambioperfil':
                try:
                    data['titulo'] = 'Menú principal'
                    mis_perfiles = None
                    # obtener perfiles

                    mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
                    data['mis_perfiles'] = mis_perfiles
                    data['tipoperfil'] = request.GET['tipoperfil']
                    act_data_aplication(request, data)
                    tipoperfil = request.session['tipoperfil']

                    menu = AccesoModulo.objects.values_list('modulo_id').filter(status=True, activo=True, grupo_id=tipoperfil)
                    modulos = Modulo.objects.filter(status=True, activo=True, pk__in=menu)
                    data['persona_logeado'] = persona_logeado
                    data['modulos'] = modulos
                    return HttpResponseRedirect("/")
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

        else:
            try:
                data['titulo'] = 'Menú principal'
                mis_perfiles = None
                #obtener perfiles
                if not 'CAM' == persona_logeado:
                    mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
                    data['mis_perfiles'] = mis_perfiles

                #obtener modulos
                if usuario_logeado.is_superuser:
                    modulos = Modulo.objects.filter(status=True,activo=True)

                else:
                    menu = AccesoModulo.objects.values_list('modulo_id').filter(status = True, activo = True ,grupo__id = tipoperfil)
                    modulos = Modulo.objects.filter(status=True, activo=True, pk__in = menu )
                data['persona_logeado'] = persona_logeado
                data['modulos'] = modulos
                return render(request, "registration/dashboard.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

def logout_usuario(request):
    logout(request)
    return HttpResponseRedirect("/login")

@transaction.atomic()
def registrate(request):
    global ex
    data = {}
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']
            if peticion == 'registrardocente':
                try:
                    if request.session.get('id') != None:  # Regístrese solo cuando no haya iniciado sesión
                        return JsonResponse({"respuesta": False, "mensaje": "Ya tiene sesión iniciada."})
                    form = RegistroUsuarioForm(request.POST)

                    if form.is_valid():
                        username = form.cleaned_data['username']
                        password = form.cleaned_data['password1']
                        nombre1 = form.cleaned_data['nombre1']
                        nombre2 = form.cleaned_data['nombre2']
                        apellido1 = form.cleaned_data['apellido1']
                        apellido2 = form.cleaned_data['apellido2']
                        cedula = form.cleaned_data['cedula']
                        genero = form.cleaned_data['genero']
                        telefono_movil = form.cleaned_data['telefono_movil']
                        telefono_convencional = form.cleaned_data['telefono_convencional']
                        email = form.cleaned_data['email']
                        username = username.strip()  # Eliminar espacios y líneas nuevas
                        password = password.strip()
                        usuario = User.objects.create_user(username, email, password)
                        usuario.save()

                        grupo = Group.objects.get(name='Docente')  # docente
                        grupo.user_set.add(usuario)
                        nombres = nombre1 + ' ' + nombre2
                        apellidos = apellido1 + ' ' + apellido2

                        persona = Persona(
                            usuario=usuario,
                            nombres=nombres,
                            apellidos=apellidos,
                            email=email,
                            cedula=cedula,
                            genero=genero,
                            telefono_movil=telefono_movil,
                            telefono_convencional=telefono_convencional
                        )
                        persona.save(request)

                        persona_perfil = PersonaPerfil(
                            persona=persona,
                            is_alumno=True
                        )
                        persona_perfil.save(request)

                        newalumno = Alumno(
                            persona=persona
                        )
                        newalumno.save(request)
                        return redirect('/login/')

                    else:
                        return render(request, "registration/registrate.html", {'form': form})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})
        return JsonResponse({"respuesta": False, "mensaje": "No se ha encontrado respuesta."})

    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']

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
            data['form'] = RegistroUsuarioForm()

    return render(request, "registration/registrate.html", data)