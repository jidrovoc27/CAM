import sys

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import PasswordChangeView
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from administrativo.models import *
from administrativo.funciones import *
from administrativo.forms import *
from academia.forms import *
from CAM import settings
from chat.models import *
from chat.forms import *
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import FormMixin
from django.views.generic import View

# Create your views here.
from django.urls import reverse_lazy


# Create your views here.
@transaction.atomic()
def verificar_clave(usuario, clave):
    user = authenticate(username=usuario, password=clave)
    if user is not None:
        # La clave es válida
        return True
    else:
        # La clave es incorrecta
        return False


@transaction.atomic()
def login_academia(request):
    global ex
    data = {}
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']
            if peticion == 'login_usuario':
                try:
                    usuario = authenticate(username=request.POST['usuario'].lower().strip(),
                                           password=request.POST['clave'])
                    if usuario is not None:
                        if usuario.is_active:
                            login(request, usuario)
                            return JsonResponse({"respuesta": True, "url": settings.LOGIN_REDIRECT_URL_ACADEMIA})
                        else:
                            return JsonResponse(
                                {"respuesta": False, 'mensaje': u'Inicio de sesión incorrecto, usuario no activo.'})
                    else:
                        return JsonResponse({"respuesta": False,
                                             'mensaje': u'Inicio de sesión incorrecto, usuario o clave no coinciden.'})
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
    if Persona.objects.filter(usuario=usuario_logeado, status=True).exists():
        persona_logeado = Persona.objects.get(usuario=usuario_logeado, status=True)
    else:
        persona_logeado = 'CAM'
    data['persona_logeado'] = persona_logeado
    data['identificadorperfil'] = identificadorperfil = request.session['identificadorperfil']
    if not 'CAM' == persona_logeado:
        mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
        data['mis_perfiles'] = mis_perfiles

    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

            if peticion == 'editperfil':
                try:
                    form = EditarPerfilForm(request.POST, request.FILES)
                    if form.is_valid():
                        persona = Persona.objects.get(id=int(request.POST['id']))
                        persona.email = form.cleaned_data['email']
                        persona.genero_id = form.cleaned_data['genero']
                        persona.telefono_movil = form.cleaned_data['telefono_movil']
                        persona.telefono_convencional = form.cleaned_data['telefono_convencional']
                        persona.ciudad = form.cleaned_data['ciudad']
                        persona.direccion = form.cleaned_data['direccion']
                        persona.referencia = form.cleaned_data['referencia']
                        persona.save(request)

                        if 'foto' in request.FILES:
                            foto = request.FILES['foto']
                            persona.foto = foto
                            persona.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Datos actualizados correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'actseguridad':
                try:
                    form = ActualizarSeguridadForm(request.POST, request.FILES)
                    if form.is_valid():
                        claveactual = form.cleaned_data['claveactual']
                        clavenueva = form.cleaned_data['clavenueva']
                        clavenuevaverifica = form.cleaned_data['clavenuevaverifica']
                        persona = Persona.objects.get(id=int(request.POST['id']))
                        usuario = User.objects.get(id=persona.usuario_id)
                        claveactualmake = verificar_clave(usuario.username, claveactual)
                        if claveactualmake:
                            if claveactual != clavenueva:
                                if clavenueva == clavenuevaverifica:
                                    usuario.set_password(clavenueva)
                                    usuario.save()
                                else:
                                    return JsonResponse(
                                        {"respuesta": False, "mensaje": "Ingrese correctamente la nueva clave"})
                            else:
                                return JsonResponse(
                                    {"respuesta": False, "mensaje": "La nueva clave debe de ser distinta a la actual"})
                        else:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Clave actual ingresada incorrectamente"})

                        return JsonResponse({"respuesta": True, "mensaje": "Clave actualizada correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'add_profile':
                try:
                    form = AgregarProfile(request.POST)
                    if form.is_valid():
                        contacto = form.cleaned_data['contacto']
                        usuario = contacto.usuario
                        persona = Persona.objects.get(id=persona_logeado.id)
                        perfil = Profile.objects.filter(user=persona.usuario)
                        if perfil:
                            perfil = perfil.first()
                            perfilusuario = Profile.objects.filter(user=usuario)
                            if perfilusuario:
                                perfilusuario = perfilusuario.first()
                                newfriend = Friend.objects.filter(profile=perfilusuario)
                                if newfriend:
                                    newfriend = newfriend.first()
                                else:
                                    newfriend = Friend(profile=perfilusuario)
                                    newfriend.save(request)
                                perfil.friends.add(newfriend)
                            else:
                                return JsonResponse(
                                    {"respuesta": False, "mensaje": "La persona no tiene perfil para contactarse"})

                        return JsonResponse({"respuesta": True, "mensaje": "Contacto añadido correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

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
                            entregatarea = NotaInscritoActividadA(inscrito_id=int(request.POST['inscrito']),
                                                                  actividad_id=int(request.POST['actividad']),
                                                                  tarea=archivo, fechasubida=datetime.now().date(),
                                                                  entregado=True)
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

            if peticion == 'add_actividad':
                try:
                    form = AgregarActividadForm(request.POST, request.FILES)
                    if form.is_valid():
                        detalle = form.cleaned_data['detalle']
                        nombre = form.cleaned_data['nombre']
                        descripcion = form.cleaned_data['descripcion']
                        minnota = form.cleaned_data['minnota']
                        maxnota = form.cleaned_data['maxnota']
                        fechamaximasubida = form.cleaned_data['fechamaximasubida']
                        horalimite = form.cleaned_data['horalimite']
                        actividad = DetalleActividadesModeloEvaluativoA(detalle=detalle, nombre=nombre,
                                                                        descripcion=descripcion, minnota=minnota,
                                                                        maxnota=maxnota,
                                                                        fechamaximasubida=fechamaximasubida,
                                                                        horalimite=horalimite)
                        actividad.save(request)
                        if 'archivo' in request.FILES:
                            archivo = request.FILES['archivo']
                            actividad.archivo = archivo
                            actividad.save(request)

                        if 'imagen' in request.FILES:
                            imagen = request.FILES['imagen']
                            actividad.imagen = imagen
                            actividad.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Actividad cargada correctamente."})
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
                        entregatarea.inscrito_id = int(request.POST['inscrito'])
                        entregatarea.actividad_id = int(request.POST['actividad'])
                        entregatarea.tarea = archivo
                        entregatarea.save(request)
                    # if len(comentario) > 0:
                    entregatarea.comentario = comentario
                    entregatarea.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Tarea actualizada correctamente."})
                    # else:
                    #     return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'edit_actividad':
                try:
                    form = AgregarActividadForm(request.POST, request.FILES)
                    # if form.is_valid():
                    actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.POST['id']))
                    detalle = request.POST['detalle']
                    nombre = request.POST['nombre']
                    descripcion = request.POST['descripcion']
                    minnota = request.POST['minnota']
                    maxnota = request.POST['maxnota']
                    fechamaximasubida = request.POST['fechamaximasubida']
                    horalimite = request.POST['horalimite']
                    actividad.detalle_id = int(detalle)
                    actividad.nombre = nombre
                    actividad.descripcion = descripcion
                    actividad.minnota = minnota
                    actividad.maxnota = maxnota
                    actividad.fechamaximasubida = fechamaximasubida
                    actividad.horalimite = horalimite
                    actividad.save(request)
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                        actividad.archivo = archivo
                        actividad.save(request)

                    if 'imagen' in request.FILES:
                        imagen = request.FILES['imagen']
                        actividad.imagen = imagen
                        actividad.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Actividad actualizada correctamente."})
                    # else:
                    #     return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_actividad':
                try:
                    actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.POST['id']))
                    actividad.status = False
                    actividad.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Actividad eliminada correctamente."})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'calificar_deber':
                try:
                    nota = request.POST['nota']
                    actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.POST['actividad']))
                    inscrito = InscritoCursoA.objects.get(id=int(request.POST['inscrito']))
                    deber = NotaInscritoActividadA.objects.filter(status=True, inscrito=inscrito, actividad=actividad)
                    if deber:
                        deber = deber.first()
                        deber.nota = Decimal(nota)
                        deber.estado = 2
                        deber.calificado = True
                        deber.save(request)
                    else:
                        newdeber = NotaInscritoActividadA(inscrito=inscrito, actividad=actividad, nota=nota, estado=2,
                                                          calificado=True)
                        newdeber.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Actividad calificada correctamente."})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Error al calificar"})
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

                    menu = AccesoModulo.objects.values_list('modulo_id').filter(status=True, activo=True,
                                                                                grupo_id=tipoperfil)
                    modulos = Modulo.objects.filter(status=True, activo=True, pk__in=menu)
                    data['persona_logeado'] = persona_logeado
                    data['modulos'] = modulos
                    return HttpResponseRedirect("/moodle/")
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

            if peticion == 'editperfil':
                try:
                    data['titulo'] = 'Editar perfil'
                    data['titulo_formulario'] = 'Editar perfil'
                    data['peticion'] = 'editperfil'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    form = EditarPerfilForm(initial={'nombres': alumno.nombres, 'apellidos': alumno.apellidos,
                                                     'email': alumno.email, 'cedula': alumno.cedula,
                                                     'genero': alumno.genero,
                                                     'telefono_movil': alumno.telefono_movil,
                                                     'telefono_convencional': alumno.telefono_convencional,
                                                     'ciudad': alumno.ciudad, 'direccion': alumno.direccion,
                                                     'referencia': alumno.referencia,
                                                     'foto': alumno.foto})
                    data['form'] = form
                    data['is_editperfil'] = True
                    return render(request, "academia/docente/edit_perfil.html", data)
                except Exception as ex:
                    pass

            if peticion == 'actseguridad':
                try:
                    data['titulo'] = 'Actualizar clave'
                    data['titulo_formulario'] = 'Actualizar clave'
                    data['peticion'] = 'actseguridad'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    form = ActualizarSeguridadForm()
                    data['form'] = form
                    data['is_security'] = True
                    return render(request, "academia/docente/edit_perfil.html", data)
                except Exception as ex:
                    pass

            if peticion == 'security':
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
                    data['inscrito'] = inscrito = InscritoCursoA.objects.filter(status=True, inscrito=alumno)
                    inscritos = inscrito.order_by('curso_id').distinct('curso_id').values_list('curso_id')
                    data['miscursos'] = CursoA.objects.filter(status=True, id__in=inscritos)
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
                        data['puedesubirtarea'] = True
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
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(
                        id=int(request.GET['id']))
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
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(
                        id=int(request.GET['id']))
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

            if peticion == 'edit_actividad':
                try:
                    data['titulo'] = 'Editar actividad'
                    data['titulo_formulario'] = 'Editar actividad'
                    data['peticion'] = 'edit_actividad'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['curso']))
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(
                        id=int(request.GET['id']))
                    form = AgregarActividadForm(initial={
                        'detalle': actividad.detalle,
                        'nombre': actividad.nombre,
                        'descripcion': actividad.descripcion,
                        'minnota': actividad.minnota,
                        'maxnota': actividad.maxnota,
                        'fechamaximasubida': actividad.fechamaximasubida,
                        'horalimite': actividad.horalimite,
                        'imagen': actividad.imagen,
                        'archivo': actividad.archivo,
                    })
                    form.fields['detalle'].queryset = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                              modelo=curso.modeloevaluativo)
                    form.sin_archivo()
                    form.sin_imagen()
                    data['form'] = form
                    return render(request, "academia/docente/edit_actividad.html", data)
                except Exception as ex:
                    pass

            if peticion == 'admcourse':
                try:
                    data['titulo'] = 'Mis cursos'
                    data['is_cursos'] = 'is_cursos'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    if 'option' in request.GET:
                        data['option'] = option = request.GET['option']
                        if option == 'summary':
                            data['detallemodelo'] = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                            modelo=curso.modeloevaluativo)
                            return render(request, "academia/docente/resumen.html", data)
                        elif option == 'participants':
                            data['inscritos'] = InscritoCursoA.objects.filter(status=True, curso=curso).order_by(
                                'inscrito__apellidos')
                            return render(request, "academia/docente/participantes.html", data)
                        elif option == 'addactv':
                            data['infoactv'] = True
                            data['actividades'] = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                          modelo=curso.modeloevaluativo)

                            if 'detalle' in request.GET:
                                data['detalle'] = detalle = int(request.GET['detalle'])
                                if detalle > 0:
                                    data['listadodetalles'] = DetalleActividadesModeloEvaluativoA.objects.filter(
                                        status=True, detalle_id=detalle)
                            return render(request, "academia/docente/actividades.html", data)

                        elif option == 'addresource':
                            data['addresource'] = True
                            data['recursos'] = RecursosCurso.objects.filter(status=True, curso=curso)

                            if 'namerecurso' in request.GET:
                                data['namerecurso'] = namerecurso = request.GET['namerecurso']
                                data['recursos'] = RecursosCurso.objects.filter(status=True, curso=curso, nombre__icontains=namerecurso)
                            return render(request, "academia/docente/recursos.html", data)
                        elif option == 'addclass':
                            data['infoclass'] = True
                            return render(request, "academia/docente/resumen.html", data)
                    else:
                        data['option'] = 'summary'
                        data['detallemodelo'] = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                        modelo=curso.modeloevaluativo)
                        return render(request, "academia/docente/resumen.html", data)
                except Exception as ex:
                    pass

            if peticion == 'calificar':
                try:
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(
                        id=int(request.GET['id']))
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['course']))
                    data['inscritos'] = InscritoCursoA.objects.filter(status=True, curso=curso).order_by(
                        'inscrito__apellidos')
                    data['alumno'] = persona_logeado
                    data['option'] = option = request.GET['option']
                    data['is_cursos'] = 'is_cursos'
                    return render(request, "academia/docente/calificar.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_actividad':
                try:
                    data['titulo'] = 'Agregar actividad'
                    data['titulo_formulario'] = 'Adicionar actividad'
                    data['peticion'] = 'add_actividad'
                    data['curso'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    form = AgregarActividadForm()
                    form.fields['detalle'].queryset = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                              modelo=cursoA.modeloevaluativo)
                    data['form'] = form
                    return render(request, "academia/docente/add_actividad.html", data)
                except Exception as ex:
                    pass

            if peticion == 'chats':
                try:
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['is_mensajes'] = 'is_mensajes'
                    if Profile.objects.filter(user=request.user):
                        user = request.user.profile
                    else:
                        user = Profile(user=request.user)
                        user.name = alumno.__str__()
                        user.pic = alumno.foto
                        user.save(request)
                    mensajes = ChatMessage.objects.filter(msg_receiver_id=user).order_by('msg_sender_id').distinct('msg_sender_id').values_list('msg_sender_id')
                    amigos = Friend.objects.filter(id__in=mensajes)
                    listado = amigos.values_list('id', flat=True)
                    existe = Profile.objects.filter(id=user.id, friend__id__in=listado)
                    if not existe:
                        usuario_recibe = Profile.objects.filter(id=user.id)
                        if usuario_recibe:
                            usuario_recibe = usuario_recibe.first()
                            for amigo in amigos:
                                existe = Profile.objects.filter(id=user.id, friend__id=amigo.id)
                                if not existe:
                                    usuario_recibe.friends.add(amigo)
                    friends = user.friends.all()
                    data['friends'] = friends
                    data['user'] = user
                    return render(request, "chat/index.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_profile':
                try:
                    data['titulo'] = 'Agregar contacto'
                    data['titulo_formulario'] = 'Adicionar contacto'
                    data['peticion'] = 'add_profile'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['inscrito'] = listadocursos = InscritoCursoA.objects.filter(status=True, inscrito=alumno).values_list('curso_id', flat=True)
                    data['inscritos'] = inscritos = InscritoCursoA.objects.filter(status=True, curso_id__in=listadocursos).exclude(inscrito=alumno).order_by('inscrito_id').distinct('inscrito_id').values_list('inscrito_id')
                    data['miscontactos'] = miscontactos = Profile.objects.get(user=alumno.usuario).friends.values_list('id', flat=True)
                    friends = Friend.objects.filter(id__in=miscontactos).values_list('profile_id', flat=True)
                    perfiles_amigos = Profile.objects.filter(id__in=friends).values_list('user_id', flat=True)
                    lista_usuarios = User.objects.filter(id__in=perfiles_amigos)
                    excluir_personas = Persona.objects.filter(status=True, usuario_id__in=lista_usuarios).values_list('id', flat=True)
                    data['personas'] = personas = Persona.objects.filter(status=True, id__in=inscritos).exclude(id__in=excluir_personas)
                    form = AgregarProfile()
                    form.fields['contacto'].queryset = personas
                    data['form'] = form
                    data['is_mensajes'] = 'is_mensajes'
                    return render(request, "chat/add_profile.html", data)
                except Exception as ex:
                    pass

            if peticion == 'chat':
                try:
                    data['is_mensajes'] = 'is_mensajes'
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    friend = Friend.objects.get(profile_id=int(request.GET['pk']))
                    user = request.user.profile
                    profile = Profile.objects.get(id=friend.profile.id)
                    chats = ChatMessage.objects.filter().order_by('id')
                    rec_chats = ChatMessage.objects.filter(msg_sender=profile, msg_receiver=user, seen=False)
                    rec_chats.update(seen=True)
                    form = ChatMessageForm()
                    if request.method == "POST":
                        form = ChatMessageForm(request.POST)
                        if form.is_valid():
                            chat_message = form.save(commit=False)
                            chat_message.msg_sender = user
                            chat_message.msg_receiver = profile
                            chat_message.save()
                            return redirect("detail", pk=friend.profile.id)
                    data['friend'] = friend
                    data['form'] = form
                    data['user'] = user
                    data['profile'] = profile
                    data['chats'] = chats
                    data['num'] = rec_chats.count()
                    return render(request, "chat/mensajeria.html", data)
                except Exception as ex:
                    pass

        else:
            try:
                data['titulo'] = 'Menú principal'
                mis_perfiles = None
                # obtener perfiles
                if identificadorperfil == 'is_alumno':
                    if not 'CAM' == persona_logeado:
                        # mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=persona_logeado)
                        # data['mis_perfiles'] = mis_perfiles
                        data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                        data['inscrito'] = inscrito = InscritoCursoA.objects.filter(status=True,
                                                                                    inscrito=alumno).order_by(
                            'curso_id').distinct('curso_id').values_list('curso_id')
                        data['miscursos'] = CursoA.objects.filter(status=True, id__in=inscrito)
                        data['is_cursos'] = True
                    return render(request, "academia/alumno/view.html", data)
                elif identificadorperfil == 'is_profesor':
                    data['alumno'] = persona = Persona.objects.get(id=persona_logeado.id)
                    data['docente'] = docente = DocenteA.objects.get(persona=persona)
                    data['miscursos'] = CursoA.objects.filter(status=True, docente=docente).order_by('-id')
                    data['is_cursos'] = True
                    return render(request, "academia/docente/view.html", data)



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
