import sys
import random

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
from academia.forms import AgregarTestForm, AgregarProfile, AgregarEntregaForm, AgregarActividadForm, AgregarRecursoForm, \
    AgregarPreguntaForm, AgregarLiteralForm
from CAM import settings
from chat.models import *
from chat.forms import *
from administrativo.templatetags.adiciones import encrypt
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import FormMixin
from django.views.generic import View
from django.http import QueryDict
from datetime import timedelta

# Create your views here.
from django.urls import reverse_lazy
from django.utils.dateparse import parse_duration


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
    data['alumno'] = alumno = persona_logeado

    if request.method == 'POST':
        if 'peticion' in request.POST:
            data['peticion'] = peticion = request.POST['peticion']

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

            if peticion == 'add_test':
                try:
                    form = AgregarTestForm(request.POST)
                    if form.is_valid():
                        detalle = request.POST['detalle']
                        tipo = int(request.POST['tipo'])
                        nombre = request.POST['nombre']
                        fecha_inicio = datetime.strptime(request.POST['fecha_inicio'], '%Y-%m-%dT%H:%M')
                        fecha_nota = datetime.strptime(request.POST['fecha_nota'], '%Y-%m-%dT%H:%M')
                        duracion = request.POST['duracion']
                        numeropregunta = int(request.POST['numeropregunta'])
                        activo = False
                        if 'activo' in request.POST:
                            activo = True

                        examen = Examen(detalle_id=detalle, tipo=tipo, nombre=nombre,
                                        fecha_inicio=fecha_inicio, fecha_nota=fecha_nota,
                                        tiempo_restante=duracion, activo=activo,
                                        duracion=duracion, numeropregunta=numeropregunta)
                        examen.save(request)
                        if tipo == 2:
                            if 'estudiantes_recuperacion' in request.POST:
                                estudiantes_recuperacion = request.POST.get('estudiantes_recuperacion')
                                for idinscrito in estudiantes_recuperacion:
                                    recuperacion = InscritosRecuperacionTest(examen=examen, inscrito_id=int(idinscrito))
                                    recuperacion.save(request)
                                examen.aplicarecuperacion = True
                                examen.save(request)
                            else:
                                return JsonResponse({"respuesta": False, "mensaje": "Por favor, elija al menos 1 estudiante"})


                        return JsonResponse({"respuesta": True, "mensaje": "Test cargada correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'add_question':
                try:
                    form = AgregarPreguntaForm(request.POST)
                    if form.is_valid():
                        idex = int(request.POST['idex'])
                        enunciado = request.POST['enunciado']
                        calificacion = Decimal(request.POST['calificacion'])

                        pregunta = Pregunta(examen_id=idex, enunciado=enunciado,
                                        calificacion=calificacion)
                        pregunta.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Pregunta registrada correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'add_literal':
                try:
                    form = AgregarLiteralForm(request.POST)
                    if form.is_valid():
                        idq = int(request.POST['idq'])
                        enunciado = request.POST['enunciado']
                        es_correcta = False

                        if 'es_correcta' in request.POST:
                            es_correcta = True

                        literal = Literal(pregunta_id=idq, texto=enunciado,
                                        es_correcta=es_correcta)
                        literal.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Literal registrado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'add_recurso':
                try:
                    form = AgregarRecursoForm(request.POST, request.FILES)
                    if form.is_valid():
                        curso = CursoA.objects.get(id=int(request.POST['id']))
                        nombre = form.cleaned_data['nombre']
                        tipo = form.cleaned_data['tipo']
                        recurso = RecursosCurso(curso=curso, nombre=nombre, tipo=int(tipo))
                        recurso.save(request)
                        if recurso.tipo == 1:
                            if 'archivo' in request.FILES:
                                archivo = form.cleaned_data['archivo']
                                recurso.archivo = archivo
                                recurso.save(request)
                                return JsonResponse({"respuesta": True, "mensaje": "Recurso cargado correctamente."})
                            else:
                                return JsonResponse({"respuesta": False, "mensaje": "Por favor, suba un archivo"})
                        else:
                            recurso.enlace = form.cleaned_data['enlace']
                            recurso.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Recurso cargado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})

            if peticion == 'edit_recurso':
                try:
                    form = AgregarRecursoForm(request.POST, request.FILES)
                    if form.is_valid():
                        recurso = RecursosCurso.objects.get(id=int(request.POST['id']))
                        nombre = request.POST['nombre']
                        tipo = request.POST['tipo']
                        recurso.nombre = nombre
                        recurso.tipo = int(tipo)
                        if recurso.tipo == 1:
                            if 'archivo' in request.FILES:
                                archivo = form.cleaned_data['archivo']
                                recurso.archivo = archivo
                            else:
                                return JsonResponse({"respuesta": False, "mensaje": "Por favor, suba un archivo"})
                        else:
                            recurso.enlace = request.POST['enlace']
                        recurso.save()
                        return JsonResponse({"respuesta": True, "mensaje": "Recurso actualizado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
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
                    transaction.set_rollback(True)
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
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'edit_test':
                try:
                    form = AgregarTestForm(request.POST)
                    # if form.is_valid():
                    examen = Examen.objects.get(id=int(request.POST['id']))
                    detalle = request.POST['detalle']
                    tipo = int(request.POST['tipo'])
                    nombre = request.POST['nombre']
                    fecha_inicio = datetime.strptime(request.POST['fecha_inicio'], '%Y-%m-%dT%H:%M')
                    fecha_nota = datetime.strptime(request.POST['fecha_nota'], '%Y-%m-%dT%H:%M')
                    duracion = request.POST['duracion']
                    numeropregunta = int(request.POST['numeropregunta'])
                    activo = False
                    if 'activo' in request.POST:
                        activo = True
                    examen.detalle_id = int(detalle)
                    examen.tipo = tipo
                    examen.nombre = nombre
                    examen.fecha_inicio = fecha_inicio
                    examen.fecha_nota = fecha_nota
                    examen.duracion = duracion
                    examen.numeropregunta = numeropregunta
                    examen.tiempo_restante = duracion
                    examen.aplicarecuperacion = False
                    examen.activo = activo
                    examen.save(request)
                    if tipo == 2:
                        if 'estudiantes_recuperacion' in request.POST:
                            estudiantes_recuperacion = request.POST.get('estudiantes_recuperacion')
                            estudiantes_asignados = []
                            for idinscrito in estudiantes_recuperacion:
                                consulta_recuperacion = InscritosRecuperacionTest.objects.filter(status=True, examen=examen, inscrito_id=int(idinscrito))
                                if not consulta_recuperacion.exists():
                                    recuperacion = InscritosRecuperacionTest(examen=examen, inscrito_id=int(idinscrito))
                                    recuperacion.save(request)
                                    estudiantes_asignados.append(recuperacion.id)
                                else:
                                    estudiantes_asignados.append(consulta_recuperacion.first().id)
                            examen.aplicarecuperacion = True
                            examen.save(request)
                            eliminar_recuperacion_inscritos = InscritosRecuperacionTest.objects.filter(status=True, examen=examen).exclude(id__in=estudiantes_asignados).delete()
                        else:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "Por favor, elija al menos 1 estudiante"})
                    else:
                        eliminar_recuperacion_inscritos = InscritosRecuperacionTest.objects.filter(status=True, examen=examen).delete()
                    return JsonResponse({"respuesta": True, "mensaje": "Test actualizado correctamente."})
                    # else:
                    #     return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'edit_question':
                try:
                    form = AgregarPreguntaForm(request.POST)
                    if form.is_valid():
                        pregunta = Pregunta.objects.get(id=int(request.POST['id']))
                        enunciado = request.POST['enunciado']
                        calificacion = Decimal(request.POST['calificacion'])
                        pregunta.enunciado = enunciado
                        pregunta.calificacion = calificacion
                        pregunta.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Pregunta actualizada correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'edit_literal':
                try:
                    form = AgregarLiteralForm(request.POST)
                    if form.is_valid():
                        literal = Literal.objects.get(id=int(request.POST['id']))
                        enunciado = request.POST['enunciado']
                        es_correcta = False
                        if 'es_correcta' in request.POST:
                            es_correcta = True
                        literal.texto = enunciado
                        literal.es_correcta = es_correcta
                        literal.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Literal actualizado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_recurso':
                try:
                    recurso = RecursosCurso.objects.get(id=int(request.POST['id']))
                    recurso.status = False
                    recurso.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Recurso eliminado correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_actividad':
                try:
                    actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.POST['id']))
                    actividad.status = False
                    actividad.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Actividad eliminada correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_test':
                try:
                    examen = Examen.objects.get(id=int(request.POST['id']))
                    examen.status = False
                    examen.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Test eliminado correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_question':
                try:
                    pregunta = Pregunta.objects.get(id=int(request.POST['id']))
                    pregunta.status = False
                    pregunta.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Pregunta eliminada correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'eliminar_literal':
                try:
                    literal = Literal.objects.get(id=int(request.POST['id']))
                    literal.status = False
                    literal.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Literal eliminado correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            if peticion == 'calificar_deber':
                try:
                    nota = Decimal(request.POST['nota'])
                    actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.POST['actividad']))
                    inscrito = InscritoCursoA.objects.get(id=int(request.POST['inscrito']))
                    deber = NotaInscritoActividadA.objects.filter(status=True, inscrito=inscrito, actividad=actividad)
                    if nota < actividad.minnota:
                        return JsonResponse({"respuesta": False, "mensaje": "La nota debe de ser mayor o igual a la nota mínima de la actividad: " + str(actividad.minnota)})
                    if deber.exists():
                        deber = deber.first()
                        deber.nota = nota
                        deber.estado = 2
                        deber.calificado = True
                        deber.save(request)
                    else:
                        newdeber = NotaInscritoActividadA(inscrito=inscrito, actividad=actividad, nota=nota, estado=2,
                                                          calificado=True)
                        newdeber.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Actividad calificada correctamente."})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Error al calificar"})

            if peticion == 'actualizar_literal':
                try:
                    es_correcta = False
                    literal = Literal.objects.get(id=int(request.POST['id']))
                    literal.es_correcta = es_correcta if literal.es_correcta else True
                    literal.save(request)
                    return JsonResponse({"respuesta": True})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": u'Error al actualizar el literal'})

            if peticion == 'marcarrespuesta':
                try:
                    literal = int(request.POST['literal'])
                    inscrito = int(request.POST['inscrito'])
                    idex = int(request.POST['idex'])
                    id = int(request.POST['id'])
                    q = int(request.POST['q'])
                    literal_selecc = Literal.objects.get(id=literal)
                    respuesta = False
                    calificacion = 0
                    examenalumno = ExamenAlumno.objects.filter(status=True, examen_id=idex, inscrito_id=inscrito)
                    examen_curso = Examen.objects.get(id=idex)
                    if examenalumno.exists():
                        examenalumno = examenalumno.first()
                        if literal_selecc.es_correcta:
                            respuesta = True
                            calificacion = literal_selecc.pregunta.calificacion
                        respuesta_alumno = RespuestaAlumno.objects.filter(status=True, examenalumno=examenalumno,
                                                                          pregunta=literal_selecc.pregunta, inscrito_id=inscrito)
                        if respuesta_alumno.exists():
                            respuesta_alumno = respuesta_alumno.first()
                            respuesta_alumno.respuesta_escogida_id = literal
                            respuesta_alumno.calificacion = calificacion
                            respuesta_alumno.save(request)
                        else:
                            respuesta_alumno = RespuestaAlumno(examenalumno=examenalumno, pregunta=literal_selecc.pregunta,
                                                               inscrito_id=inscrito, respuesta_escogida_id=literal,
                                                               calificacion=calificacion)
                            respuesta_alumno.save(request)
                        preguntas_seleccionadas = examen_curso.consultar_preguntas_asignadas(inscrito).values_list('id', flat=True)
                        siguiente_pregunta = Pregunta.objects.filter(status=True, id__in=preguntas_seleccionadas, id__gt=q).order_by('id')
                        if siguiente_pregunta.exists():
                            siguiente_pregunta = siguiente_pregunta.first()
                            return redirect('/moodle/?peticion=rendirexamen&id=%s' % encrypt(id) + '&inscrito=%s' % encrypt(inscrito) + '&idex=%s' % encrypt(idex) + '&q=%s' % encrypt(siguiente_pregunta.id), 200)
                        else:
                            return redirect(
                                '/moodle/?peticion=revision&id=%s' % encrypt(id) + '&inscrito=%s' % encrypt(inscrito) + '&idex=%s' % encrypt(idex),200)
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Error al elegir la respuesta"})

            if peticion == 'enviaryterminar':
                try:
                    id = int(request.POST['id'])
                    idex = int(request.POST['idex'])
                    inscrito = int(request.POST['inscrito'])
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)
                    notafinal = 0
                    examenalumno = ExamenAlumno.objects.filter(status=True, examen_id=idex, inscrito_id=inscrito)
                    examen_curso = Examen.objects.get(id=idex)
                    if examenalumno.exists():
                        examenalumno = examenalumno.first()
                        preguntas = examen_curso.consultar_preguntas_asignadas(inscrito)
                        for pregunta in preguntas:
                            calificacion = pregunta.calificacion
                            literalcorrecto = Literal.objects.filter(status=True, pregunta=pregunta, es_correcta=True)
                            if literalcorrecto.exists():
                                literalcorrecto = literalcorrecto.first()
                                pregunta_fue_contestada = RespuestaAlumno.objects.filter(status=True, examenalumno=examenalumno, pregunta=pregunta)
                                if pregunta_fue_contestada.exists():
                                    respuesta_alumno = pregunta_fue_contestada.first()
                                    calificacion = calificacion if respuesta_alumno.respuesta_escogida == literalcorrecto else 0
                                    respuesta_alumno.es_correcta = True if respuesta_alumno.respuesta_escogida == literalcorrecto else False
                                    respuesta_alumno.calificacion = calificacion
                                    respuesta_alumno.save(request)
                                    notafinal += calificacion
                        examenalumno.estado = 2
                        examenalumno.fecha_termina = fechaactual
                        examenalumno.calificacionfinal = notafinal
                        examenalumno.save(request)
                        #CREA LA NOTA PARA PROMEDIAR
                        notaexamen = NotaInscritoActividadA.objects.filter(status=True, inscrito_id=inscrito, examen_id=idex)
                        if not notaexamen.exists():
                            notaexamen = NotaInscritoActividadA(inscrito_id=inscrito, examen_id=idex, nota=notafinal)
                            notaexamen.save(request)
                        return redirect('/moodle/?peticion=verexamen&id=%s' % id + '&inscrito=%s' % inscrito + '&idex=%s' % idex, 200)
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Error al enviar el cuestionario"})


    else:
        if 'peticion' in request.GET:
            data['peticion'] = peticion = request.GET['peticion']

            if peticion == 'actualizar_tiempo':
                try:
                    examen = Examen.objects.get(pk=int(request.GET['id']))
                    tiempo_restante = query_dict = QueryDict(request.GET['tiempo_restante'])
                    diccionario = query_dict.dict()
                    valor_numerico = request.GET['tiempo_restante']
                    # delta_tiempo = timedelta(seconds=valor_numerico)

                    # Actualizar el campo "tiempo_restante" del examen
                    duracion_str = valor_numerico
                    horas, minutos, segundos = duracion_str.split(':')
                    duracion = timedelta(hours=int(horas), minutes=int(minutos), seconds=int(segundos))
                    examen.tiempo_restante = duracion
                    examen.save()
                    data['examen'] = examen
                    return JsonResponse({'success': True})
                except Exception as ex:
                    return JsonResponse({'success': False})

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
                    data['rubros'] = Rubro.objects.filter(status=True, persona=persona).order_by('-id')
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
                    data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=idactividad)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=int(request.GET['inscrito']))
                    data['cursoA'] = cursoA = CursoA.objects.get(id=int(request.GET['curso']))
                    nota = NotaInscritoActividadA.objects.filter(status=True, inscrito=inscrito, actividad=actividad)
                    if nota.exists():
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

            if peticion == 'verexamen':
                try:
                    idex = int(request.GET['idex'])
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)
                    data['examen'] = examen = Examen.objects.get(id=idex)
                    data['fecha_final'] = examen.fecha_inicio + timedelta(seconds=examen.duracion.seconds)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=int(request.GET['inscrito']))
                    data['cursoA'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    data['examenesrendidos'] = examenesrendidos = ExamenAlumno.objects.filter(status=True, inscrito=inscrito, examen=examen)
                    data['is_calificaciones'] = True
                    return render(request, "academia/calificaciones/verexamen.html", data)
                except Exception as ex:
                    pass

            if peticion == 'rendirexamen':
                try:
                    #PARÁMETROS QUE RECIBO POR GET
                    idex = int(encrypt(request.GET['idex']))
                    idinscrito = int(encrypt(request.GET['inscrito']))
                    idcurso = int(encrypt(request.GET['id']))

                    #CONSULTO LA FECHA ACTUAL
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)

                    #CONSULTO EL EXAMEN CON SUS RESPECTIVAS PREGUNTAS
                    data['examen'] = examen = Examen.objects.get(id=idex)
                    totalpreguntas = examen.pregunta_set.filter(status=True).order_by('id')

                    #VERIFICO SI EL INSCRITO YA RINDIÓ EL EXAMEN O SI NO EXISTEN PREGUNTAS O SI LA FECHA PARA DAR LA PRUEBA YA PASÓ
                    comienzoexamen = ExamenAlumno.objects.filter(status=True, examen=examen, inscrito_id=idinscrito)
                    if examen.rindio_examen(idinscrito) or not totalpreguntas.exists() or fechaactual > examen.fecha_limite_examen():
                        examen.calcular_notafinal(idinscrito, fechaactual, request)
                        return redirect('/moodle/?peticion=verexamen&id=%s' % idcurso + '&inscrito=%s' %idinscrito + '&idex=%s' % idex)

                    #CABECERA EXAMEN DEL ALUMNO
                    if not comienzoexamen.exists():
                        comienzoexamen = ExamenAlumno(examen=examen, inscrito_id=idinscrito, fecha_inicio=fechaactual)
                        comienzoexamen.save(request)

                    #VERIFICO SI EXISTE EL NÚMERO DE PREGUNTAS PARA SELECCIONAR ALEATORIAMENTE
                    if totalpreguntas.count() < examen.numeropregunta:
                        return redirect('/moodle/?peticion=verexamen&id=%s' % idcurso + '&inscrito=%s' % idinscrito + '&idex=%s' % idex)
                    preguntas_asignadas = examen.generar_preguntas_aleatorias(idinscrito, request)
                    preguntas = preguntas_asignadas
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=idinscrito)
                    data['cursoA'] = cursoA = CursoA.objects.get(id=idcurso)
                    if 'q' in request.GET:
                        data['q'] = q = int(encrypt(request.GET['q']))
                        preguntarecibida = Pregunta.objects.filter(id=q)
                        if preguntarecibida.exists():
                            preguntaactual = preguntarecibida.first()
                        else:
                            preguntaactual = preguntas.first()
                    else:
                        preguntaactual = preguntas.first()
                        data['q'] = preguntaactual.id
                    data['preguntaactual'] = preguntaactual
                    data['preguntas'] = preguntas
                    return render(request, "academia/calificaciones/rendirexamen.html", data)

                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            if peticion == 'revision':
                try:
                    idex = int(encrypt(request.GET['idex']))
                    idinscrito = int(encrypt(request.GET['inscrito']))
                    idcurso = int(encrypt(request.GET['id']))
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)
                    data['examen'] = examen = Examen.objects.get(id=idex)
                    data['preguntas'] = preguntas = examen.consultar_preguntas_asignadas(idinscrito)
                    if examen.rindio_examen(idinscrito) or not preguntas.exists() or fechaactual > examen.fecha_limite_examen():
                        return redirect('/moodle/?peticion=verexamen&id=%s' % idcurso + '&inscrito=%s' % idinscrito + '&idex=%s' % idex)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=idinscrito)
                    data['cursoA'] = cursoA = CursoA.objects.get(id=idcurso)
                    if 'q' in request.GET:
                        data['q'] = q = int(encrypt(request.GET['q']))
                        preguntarecibida = Pregunta.objects.filter(id=q)
                        if preguntarecibida.exists():
                            preguntaactual = preguntarecibida.first()
                        else:
                            preguntaactual = preguntas.first()
                    else:
                        preguntaactual = preguntas.first()
                        data['q'] = preguntaactual.id
                    data['preguntaactual'] = preguntaactual
                    return render(request, "academia/calificaciones/finalizar.html", data)
                except Exception as ex:
                    pass

            if peticion == 'reviewanswers':
                try:
                    idex = int(encrypt(request.GET['idex']))
                    idinscrito = int(encrypt(request.GET['inscrito']))
                    idcurso = int(encrypt(request.GET['id']))
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)
                    data['examen'] = examen = Examen.objects.get(id=idex)
                    data['preguntas'] = preguntas = examen.consultar_preguntas_asignadas(idinscrito)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=idinscrito)
                    data['cursoA'] = cursoA = CursoA.objects.get(id=idcurso)
                    if preguntas:
                        if 'q' in request.GET:
                            data['q'] = q = int(encrypt(request.GET['q']))
                            preguntarecibida = Pregunta.objects.filter(id=q)
                            if preguntarecibida.exists():
                                preguntaactual = preguntarecibida.first()
                            else:
                                preguntaactual = preguntas.first()
                        else:
                            preguntaactual = preguntas.first()
                            data['q'] = preguntaactual.id
                        data['preguntaactual'] = preguntaactual
                        return render(request, "academia/calificaciones/revisionexamen.html", data)
                    return redirect('/moodle/?peticion=verexamen&id=%s' % idcurso + '&inscrito=%s' % idinscrito + '&idex=%s' % idex)
                except Exception as ex:
                    pass

            if peticion == 'revisionexamen':
                try:
                    idex = int(encrypt(request.GET['idex']))
                    idinscrito = int(encrypt(request.GET['inscrito']))
                    idcurso = int(encrypt(request.GET['id']))
                    data['fechaactual'] = fechaactual = datetime.now().replace(microsecond=0)
                    data['examen'] = examen = Examen.objects.get(id=idex)
                    data['preguntas'] = preguntas = examen.consultar_preguntas_asignadas(idinscrito)
                    data['inscrito'] = inscrito = InscritoCursoA.objects.get(id=idinscrito)
                    data['cursoA'] = cursoA = CursoA.objects.get(id=idcurso)
                    if 'q' in request.GET:
                        data['q'] = q = int(encrypt(request.GET['q']))
                        preguntarecibida = Pregunta.objects.filter(id=q)
                        if preguntarecibida.exists():
                            preguntaactual = preguntarecibida.first()
                        else:
                            preguntaactual = preguntas.first()
                    else:
                        preguntaactual = preguntas.first()
                        data['q'] = preguntaactual.id
                    data['preguntaactual'] = preguntaactual
                    return render(request, "academia/calificaciones/revisionexamendocente.html", data)
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

            if peticion == 'edit_recurso':
                try:
                    data['titulo'] = 'Editar recurso'
                    data['titulo_formulario'] = 'Editar recurso'
                    data['peticion'] = 'edit_recurso'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['curso']))
                    data['recurso'] = recurso = RecursosCurso.objects.get(id=int(request.GET['id']))
                    form = AgregarRecursoForm(initial={
                        'nombre': recurso.nombre,
                        'tipo': recurso.tipo,
                        'archivo': recurso.archivo,
                        'enlace': recurso.enlace,
                    })
                    data['form'] = form
                    return render(request, "academia/docente/edit_recurso.html", data)
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

            if peticion == 'edit_test':
                try:
                    data['titulo'] = 'Editar test'
                    data['titulo_formulario'] = 'Editar test'
                    data['peticion'] = 'edit_test'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['curso']))
                    data['examen'] = examen = Examen.objects.get(id=int(request.GET['id']))
                    form = AgregarTestForm(initial={
                        'detalle': examen.detalle,
                        'tipo': examen.tipo,
                        'nombre': examen.nombre,
                        'fecha_inicio': examen.fecha_inicio,
                        'fecha_nota': examen.fecha_nota,
                        'duracion': examen.duracion,
                        'numeropregunta': examen.numeropregunta,
                        'activo': examen.activo,
                    })
                    inscritos = curso.inscritocursoa_set.filter(status=True)
                    data['inscritos'] = inscritos.order_by('inscrito__apellidos') if inscritos.exists() else inscritos
                    lista_inscritos = InscritosRecuperacionTest.objects.filter(status=True, examen=examen)
                    data['lista_inscritos'] = lista_inscritos.values_list('inscrito_id', flat=True)
                    form.fields['detalle'].queryset = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=curso.modeloevaluativo)
                    data['form'] = form
                    return render(request, "academia/docente/edit_test.html", data)
                except Exception as ex:
                    pass

            if peticion == 'edit_question':
                try:
                    data['titulo'] = 'Editar pregunta'
                    data['titulo_formulario'] = 'Editar pregunta'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['pregunta'] = pregunta = Pregunta.objects.get(id=int(request.GET['idq']))
                    form = AgregarPreguntaForm(initial={
                        'enunciado': pregunta.enunciado,
                        'calificacion': pregunta.calificacion
                    })
                    data['form'] = form
                    return render(request, "academia/docente/edit_question.html", data)
                except Exception as ex:
                    pass

            if peticion == 'edit_literal':
                try:
                    data['titulo'] = 'Editar literal'
                    data['titulo_formulario'] = 'Editar literal'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['literal'] = literal = Literal.objects.get(id=int(request.GET['idli']))
                    form = AgregarLiteralForm(initial={
                        'enunciado': literal.texto,
                        'es_correcta': literal.es_correcta
                    })
                    data['form'] = form
                    return render(request, "academia/docente/edit_literal.html", data)
                except Exception as ex:
                    pass

            if peticion == 'admcourse':
                try:
                    data['titulo'] = 'Mis cursos'
                    data['is_cursos'] = 'is_cursos'
                    if mis_perfiles.first().is_profesor == False:
                        return redirect('/moodle/?peticion=viewcurso&id=%s' % request.GET['id'])
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
                        elif option == 'addtest':
                            data['addtest'] = True
                            data['actividades'] = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=curso.modeloevaluativo)

                            if 'detalle' in request.GET:
                                data['detalle'] = detalle = int(request.GET['detalle'])
                                if detalle > 0:
                                    data['examenes'] = Examen.objects.filter(status=True, detalle_id=detalle)
                            return render(request, "academia/docente/tests.html", data)

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

            if peticion == 'questions':
                try:
                    data['titulo'] = 'Preguntas'
                    if mis_perfiles.first().is_profesor == False:
                        return redirect('/moodle/?peticion=viewcurso&id=%s' % request.GET['id'])
                    data['is_cursos'], data['option'], filtro = 'is_cursos', 'addtest', Q(status=True)
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['examen'] = examen = Examen.objects.get(id=int(request.GET['idex']))
                    filtro = filtro & Q(examen=examen)
                    if 'busqueda' in request.GET:
                        data['busqueda'] = busqueda = request.GET['busqueda']
                        filtro = filtro & Q(enunciado__icontains=busqueda)
                    data['preguntas'] = preguntas = Pregunta.objects.filter(filtro)
                    return render(request, "academia/docente/preguntas.html", data)
                except Exception as ex:
                    pass

            if peticion == 'literals':
                try:
                    data['titulo'] = 'Literales'
                    if mis_perfiles.first().is_profesor == False:
                        return redirect('/moodle/?peticion=viewcurso&id=%s' % request.GET['id'])
                    data['is_cursos'], data['option'], filtro = 'is_cursos', 'addtest', Q(status=True)
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['pregunta'] = pregunta = Pregunta.objects.get(id=int(request.GET['idq']))
                    filtro = filtro & Q(pregunta=pregunta)
                    if 'busqueda' in request.GET:
                        data['busqueda'] = busqueda = request.GET['busqueda']
                        filtro = filtro & Q(texto__icontains=busqueda)
                    data['literales'] = literales = Literal.objects.filter(filtro).order_by('-id')
                    return render(request, "academia/docente/literales.html", data)
                except Exception as ex:
                    pass

            if peticion == 'viewcurso':
                try:
                    data['titulo'] = 'Mis cursos'
                    data['is_cursos'] = 'is_cursos'
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['id']))
                    data['alumno'] = alumno = Persona.objects.get(id=persona_logeado.id)
                    data['inscrito'] = InscritoCursoA.objects.get(status=True, curso=curso, inscrito=alumno)
                    data['option'] = 'summary'
                    data['detallemodelo'] = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=curso.modeloevaluativo)
                    return render(request, "academia/docente/viewcurso.html", data)
                except Exception as ex:
                    pass

            if peticion == 'calificar':
                try:
                    data['curso'] = curso = CursoA.objects.get(id=int(request.GET['course']))
                    data['inscritos'] = InscritoCursoA.objects.filter(status=True, curso=curso).order_by('inscrito__apellidos')
                    data['option'] = option = request.GET['option']
                    data['is_cursos'] = 'is_cursos'
                    if 'id' in request.GET:
                        data['actividad'] = actividad = DetalleActividadesModeloEvaluativoA.objects.get(id=int(request.GET['id']))
                        return render(request, "academia/docente/calificar.html", data)
                    elif 'idex' in request.GET:
                        data['examen'] = examen = Examen.objects.get(id=int(request.GET['idex']))
                        return render(request, "academia/docente/calificarexamen.html", data)
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

            if peticion == 'add_test':
                try:
                    data['titulo'] = 'Agregar test'
                    data['titulo_formulario'] = 'Adicionar test'
                    data['peticion'] = 'add_test'
                    data['curso'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    inscritos = cursoA.inscritocursoa_set.filter(status=True)
                    data['inscritos'] = inscritos.order_by('inscrito__apellidos') if inscritos.exists() else inscritos
                    form = AgregarTestForm()
                    form.fields['detalle'].queryset = DetalleModeloEvaluativoA.objects.filter(status=True,
                                                                                              modelo=cursoA.modeloevaluativo)
                    data['form'] = form
                    return render(request, "academia/docente/add_test.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_question':
                try:
                    data['titulo'] = 'Agregar pregunta'
                    data['titulo_formulario'] = 'Adicionar pregunta'
                    data['peticion'] = 'add_question'
                    data['curso'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    data['examen'] = examen = Examen.objects.get(id=int(request.GET['idex']))
                    form = AgregarPreguntaForm()
                    data['form'] = form
                    return render(request, "academia/docente/add_question.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_literal':
                try:
                    data['titulo'] = 'Agregar literal'
                    data['titulo_formulario'] = 'Adicionar literal'
                    data['peticion'] = 'add_literal'
                    data['curso'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    data['pregunta'] = pregunta = Pregunta.objects.get(id=int(request.GET['idq']))
                    form = AgregarLiteralForm()
                    data['form'] = form
                    return render(request, "academia/docente/add_literal.html", data)
                except Exception as ex:
                    pass

            if peticion == 'add_recurso':
                try:
                    data['titulo'] = 'Agregar recurso'
                    data['titulo_formulario'] = 'Adicionar recurso'
                    data['peticion'] = 'add_recurso'
                    data['curso'] = cursoA = CursoA.objects.get(id=int(request.GET['id']))
                    form = AgregarRecursoForm()
                    data['form'] = form
                    return render(request, "academia/docente/add_recurso.html", data)
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
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": ex.__str__()})

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

            if peticion == 'rendir_examen':
                try:
                    data['examen'] = examen = Examen.objects.get(pk=int(request.GET['id']))
                    tiempo_restante = (examen.hora_inicio - timezone.now()).total_seconds()
                    data['tiempo_restante_segundos'] = examen.tiempo_restante.total_seconds()
                    return render(request, 'academia/examen/examen.html', data)
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
                    docente = DocenteA.objects.filter(persona=persona)
                    if docente.exists():
                        docente = docente.first()
                        data['docente'] = docente
                        data['miscursos'] = CursoA.objects.filter(status=True, docente=docente).order_by('-id')
                        data['is_cursos'] = True
                        return render(request, "academia/docente/view.html", data)
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
