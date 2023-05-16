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
from academia.forms import *
from CAM import settings

# Create your views here.
from django.urls import reverse_lazy

# Create your views here.

@transaction.atomic()
def login_academia(request):
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
                            login(request, usuario)
                            return JsonResponse({"respuesta": True, "url": settings.LOGIN_REDIRECT_URL_ACADEMIA})
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

@login_required(redirect_field_name='next', login_url='/loginacademia/')
@transaction.atomic()
def dashboard(request):
    global ex
    data = {}
    add_data_aplication_academia(request, data)
    usuario_logeado = request.user
    if  Persona.objects.filter(usuario=usuario_logeado, status=True).exists():
        persona_logeado = Persona.objects.get(usuario=usuario_logeado, status=True)
    else:
        persona_logeado = 'CAM'

    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

            if peticion == 'add_tarea':
                try:
                    form = AgregarEntregaForm(request.POST, request.FILES)
                    if form.is_valid():
                        comentario = form.cleaned_data['comentario']
                        if 'archivo' in request.FILES:
                            archivo = request.FILES['archivo']
                            # newfilesd = archivo._name
                            # ext = newfilesd[newfilesd.rfind("."):]
                            # if not ext == '.docx' or not ext == '.pdf':
                            #     return JsonResponse({"respuesta": False, "mensaje": "La tarea es en formato .docx o .pdf"})
                            entregatarea = NotaInscritoActividadA(inscrito_id=int(request.POST['inscrito']), actividad_id=int(request.POST['actividad']),
                                                                  tarea=archivo, fechasubida=datetime.now().date())
                            entregatarea.save(request)
                            if len(comentario) > 0:
                                entregatarea.comentario = comentario
                                entregatarea.save(request)
                        else:
                            return JsonResponse({"respuesta": False, "mensaje": "Por favor, suba la tarea."})
                        return JsonResponse({"respuesta": True, "mensaje": "Tarea cargada correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'edit_tarea':
                try:
                    form = AgregarEntregaForm(request.POST, request.FILES)
                    # if form.is_valid():
                    entregatarea = NotaInscritoActividadA.objects.get(id=int(request.POST['id']))
                    comentario = request.POST['comentario']
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                        entregatarea.inscrito_id=int(request.POST['inscrito'])
                        entregatarea.actividad_id=int(request.POST['actividad'])
                        entregatarea.tarea=archivo
                        entregatarea.save(request)
                    # if len(comentario) > 0:
                    entregatarea.comentario = comentario
                    entregatarea.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Tarea actualizada correctamente."})
                    # else:
                    #     return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})
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
                    act_data_aplication_academia(request, data)
                    tipoperfil = request.session['tipoperfil']

                    menu = AccesoModulo.objects.values_list('modulo_id').filter(status=True, activo=True, grupo_id=tipoperfil)
                    modulos = Modulo.objects.filter(status=True, activo=True, pk__in=menu)
                    data['persona_logeado'] = persona_logeado
                    data['modulos'] = modulos
                    return HttpResponseRedirect("/loginacademia/inicio/")
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

            if peticion == 'misfinanzas':
                try:
                    idpersona = int(request.GET['id'])
                    data['persona'] = persona = Persona.objects.get(id=idpersona)
                    data['alumno'] = persona
                    data['rubros'] = Rubro.objects.filter(status=True, persona=persona)
                    data['is_finanza'] = True
                    return render(request, "academia/misfinanzas/view.html", data)
                except Exception as ex:
                    pass

            if peticion == 'calificaciones':
                try:
                    idpersona = int(request.GET['id'])
                    data['alumno'] = alumno = Persona.objects.get(id=idpersona)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.filter(status=True, inscrito=alumno).order_by('curso_id').distinct('curso_id').values_list('curso_id')
                    data['miscursos'] = CursoA.objects.filter(status=True, id__in=inscrito)
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/view.html", data)
                except Exception as ex:
                    pass

            if peticion == 'detallecalificacion':
                try:
                    idcurso = int(request.GET['id'])
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['cursoA'] = curso = CursoA.objects.get(status=True, id=idcurso)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(status=True, curso=curso, inscrito=alumno)
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/detallecalificacion.html", data)
                except Exception as ex:
                    pass

            if peticion == 'actividad':
                try:
                    idactividad = int(request.GET['id'])
                    fechaactual = datetime.now().date()
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=idactividad)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=int(request.GET['inscrito']))
                    data['cursoA'] = cursoA = CursoA.objects.get(id=int(request.GET['curso']))
                    nota = NotaInscritoActividadA.objects.filter(status=True, inscrito=inscrito, actividad=actividad)
                    if nota:
                        data['nota'] = nota.first()
                    else:
                        data['nota'] = False
                    data['tiemporestante'] = 'Fecha de entrega ya pasó'
                    if actividad.fechamaximasubida > fechaactual:
                        fecharestante = actividad.fechamaximasubida - fechaactual
                        numerodias = fecharestante.days
                        numerosegundos = fecharestante.seconds
                        numerohoras = numerosegundos // 3600
                        data['tiemporestante'] = str(numerodias) + " días " + str(numerohoras) + " horas"
                    if actividad.fechamaximasubida == fechaactual:
                        fecharestante = actividad.fechamaximasubida - fechaactual
                        numerodias = fecharestante.days
                        numerosegundos = fecharestante.seconds
                        numerohoras = numerosegundos // 3600
                        data['puedesubirtarea'] = False
                        if actividad.horalimite.hour >= datetime.now().hour:
                            horalimite = actividad.horalimite.hour - datetime.now().hour
                        else:
                            horalimite = 0
                        if horalimite > 0:
                            data['puedesubirtarea'] = True
                            data['tiemporestante'] = str(numerodias) + " días " + str(horalimite) + " horas"
                        else:
                            data['puedesubirtarea'] = True if numerohoras > 0 else False
                            data['tiemporestante'] = str(numerodias) + " días " + str(numerohoras) + " horas"
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/actividad.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_tarea':
                try:
                    data['titulo'] = 'Agregar entrega'
                    data['titulo_formulario'] = 'Adicionar entrega de la tarea'
                    data['peticion'] = 'add_tarea'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.GET['id']))
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=int(request.GET['inscrito']))
                    data['cursoA'] = cursoA = CursoA.objects.get(id=int(request.GET['curso']))
                    form = AgregarEntregaForm()
                    data['form'] = form
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/add_tarea.html", data)
                except Exception as ex:
                    pass

            if peticion == 'edit_tarea':
                try:
                    data['titulo'] = 'Editar entrega'
                    data['titulo_formulario'] = 'Editar entrega de la tarea'
                    data['peticion'] = 'edit_tarea'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.GET['id']))
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=int(request.GET['inscrito']))
                    data['cursoA'] = cursoA = CursoA.objects.get(id=int(request.GET['curso']))
                    data['nota'] = nota = NotaInscritoActividadA.objects.get(id=int(request.GET['nota']))
                    form = AgregarEntregaForm(initial={
                        'archivo': nota.tarea,
                        'comentario': nota.comentario
                    })
                    form.sin_archivo()
                    data['form'] = form
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/edit_tarea.html", data)
                except Exception as ex:
                    pass

        else:
            try:
                data['titulo'] = 'Menú principal'
                mis_perfiles = None
                #obtener perfiles
                if not 'CAM' == persona_logeado:
                    mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
                    data['mis_perfiles'] = mis_perfiles
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.filter(status=True, inscrito=alumno).order_by('curso_id').distinct('curso_id').values_list('curso_id')
                    data['miscursos'] = CursoA.objects.filter(status=True, id__in=inscrito)
                    data['is_cursos'] = True
                data['persona_logeado'] = persona_logeado
                return render(request, "academia/alumno/view.html", data)


            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

def logout_usuario(request):
    logout(request)
    return HttpResponseRedirect("/loginacademia/")

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

                        grupo = Group.objects.get(pk=4)  # docente
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