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
from CAM.settings import ALMACENAMIENTO
from CAM.settings import BASE_DIR, MEDIA_ROOT
from administrativo.forms import *
from administrativo.funciones import *
from administrativo.models import *
from academia.models import *
from django.db.models import Q

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

def redimenzionar_imagen(ruta_original, ruta_a_guardar, ancho, alto):
    from PIL import Image

    # Abre la imagen que quieres redimensionar
    imagen = Image.open(ruta_original)

    # Define el nuevo tamaño deseado para la imagen
    nuevo_tamaño = (ancho, alto)  # (ancho, alto)

    # Redimensiona la imagen con el nuevo tamaño
    imagen_redimensionada = imagen.resize(nuevo_tamaño)

    # Guarda la nueva imagen redimensionada
    imagen_redimensionada.save(ruta_a_guardar)

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_periodo(request):
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

            if peticion == 'add_periodo':
                try:
                    form = PeriodoForm(request.POST, request.FILES)
                    if form.is_valid():

                        campos_repetidos = list()

                        if Periodo.objects.values('id').filter(nombre=form.cleaned_data['nombre'], status=True).exists():
                            campos_repetidos.append(form['nombre'].name)
                        if campos_repetidos:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "registro ya existe.", 'repetidos': campos_repetidos})
                        nombre = form.cleaned_data['nombre']
                        descripcion = form.cleaned_data['descripcion']
                        inicio = form.cleaned_data['inicio']
                        fin = form.cleaned_data['fin']
                        activo = form.cleaned_data['activo']

                        newperiodo = Periodo(nombre=nombre, descripcion=descripcion, inicio=inicio, fin=fin, activo=activo)
                        newperiodo.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                       return JsonResponse(  {"respuesta": False, "mensaje": form.errors.items()})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'edit_periodo':
                try:
                    form = PeriodoForm(request.POST, request.FILES)
                    if form.is_valid():
                        periodo = Periodo.objects.get(pk=request.POST['id'])
                        periodo.nombre =request.POST['nombre']
                        periodo.descripcion=request.POST['descripcion']
                        periodo.inicio=request.POST['inicio']
                        periodo.fin=request.POST['fin']
                        if 'activo' in request.POST:
                            periodo.activo = True if request.POST['activo'] == 'on' else False
                        else:
                            periodo.activo = False
                        periodo.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro Modificado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            elif peticion == 'add_curso':
                try:
                    form = CursoForm(request.POST, request.FILES)
                    if form.is_valid():

                        periodo = form.cleaned_data['periodo']
                        docente = form.cleaned_data['docente']
                        nombre = form.cleaned_data['nombre']
                        tiporubro = form.cleaned_data['tiporubro']
                        costo = form.cleaned_data['costo']
                        fechainicio = form.cleaned_data['fechainicio']
                        fechafin = form.cleaned_data['fechafin']
                        fechainicioinscripcion = form.cleaned_data['fechainicioinscripcion']
                        fechafininscripcion = form.cleaned_data['fechafininscripcion']
                        gcuotas = form.cleaned_data['gcuotas']
                        oferta = form.cleaned_data['oferta']
                        inscripcion = form.cleaned_data['inscripcion']
                        matricula = form.cleaned_data['matricula']
                        horasvirtual = form.cleaned_data['horasvirtual']
                        minasistencia = form.cleaned_data['minasistencia']
                        minnota = form.cleaned_data['minnota']
                        cupo = form.cleaned_data['cupo']
                        observacion = form.cleaned_data['observacion']
                        objetivo = form.cleaned_data['objetivo']
                        contenido = form.cleaned_data['contenido']
                        publicarcurso = form.cleaned_data['publicarcurso']
                        planificacion = request.FILES['planificacion']
                        imagen = request.FILES['imagen']
                        imagenweb = request.FILES['imagenweb']

                        curso = Curso(periodo=periodo, docente=docente, nombre=nombre, tiporubro=tiporubro, costo=costo,
                                      fechainicio=fechainicio, fechafin=fechafin, fechainicioinscripcion=fechainicioinscripcion, fechafininscripcion=fechafininscripcion,
                                      horasvirtual=horasvirtual, minasistencia=minasistencia, minnota=minnota, cupo=cupo,
                                      observacion=observacion, objetivo=objetivo, contenido=contenido, publicarcurso=publicarcurso, gcuotas=gcuotas, oferta=oferta, estado=2)

                        #VERIFICA SI EL CURSO APLICA INSCRIPCIÓN
                        if inscripcion:
                            curso.inscripcion = True
                            curso.tiporubroinscripcion = form.cleaned_data['tiporubroinscripcion']
                            curso.costoinscripcion = form.cleaned_data['costoinscripcion']

                        # VERIFICA SI EL CURSO APLICA MATRÍCULA
                        if matricula:
                            curso.matricula = True
                            curso.tiporubromatricula = form.cleaned_data['tiporubromatricula']
                            curso.costomatricula = form.cleaned_data['costomatricula']

                        curso.save(request)

                        if curso.gcuotas:
                            if 'valor' in request.POST:
                                inicios = request.POST.getlist('inicio')
                                fines = request.POST.getlist('fin')
                                valores = request.POST.getlist('valor')
                                tiporubrocuota = form.cleaned_data['tiporubrocuota']
                                curso.tiporubrocuota = tiporubrocuota
                                numcuota = 1
                                contador = 0
                                for cuota in inicios:
                                    nuevacuota = CuotasCurso(curso=curso, numerocuota=numcuota, inicio=inicios[contador],
                                                             fin=fines[contador], valor=valores[contador])
                                    nuevacuota.save(request)
                                    numcuota += 1
                                    contador += 1
                                curso.cuotas = numcuota
                                curso.save(request)
                            else:
                                transaction.set_rollback(True)
                                return JsonResponse({"respuesta": False, "mensaje": "Por favor, ingrese las cuotas correspondientes."})

                        if curso.oferta:
                            costooferta = form.cleaned_data['costooferta']
                            curso.costooferta = costooferta
                            curso.save(request)

                        #GUARDA LA PLANIFICACIÓN DEL CURSO
                        if 'planificacion' in request.FILES:
                            newfile = request.FILES['planificacion']
                            newfile._name = nuevo_nombre("planificacion", newfile._name)
                            curso.planificacion = newfile
                            curso.save(request)

                        #GUARDA LA IMAGEN DEL CURSO QUE SIRVE PARA LA PÁGINA WEB
                        if 'imagenweb' in request.FILES:
                            newfile = request.FILES['imagenweb']
                            newfile._name = nuevo_nombre("imagenweb", newfile._name)
                            curso.fondoweb = newfile
                            curso.save(request)
                            rutaweb = MEDIA_ROOT + '/fondoweb/' + newfile._name
                            ruta_a_guardar_web = MEDIA_ROOT + '/fondoweb/' + newfile._name
                            redimenzionar_imagen(rutaweb, ruta_a_guardar_web, 693, 843)
                            curso.save(request)

                        # GUARDA LA IMAGEN DEL CURSO QUE SIRVE PARA LA PARTE ACADÉMICA
                        if 'imagen' in request.FILES:
                            newfile = request.FILES['imagen']
                            newfile._name = nuevo_nombre("imagen", newfile._name)
                            curso.fondocursos = newfile
                            curso.save(request)
                            rutacursos = MEDIA_ROOT + '/fondocursos/' + newfile._name
                            ruta_a_guardar_cursos = MEDIA_ROOT + '/fondocursos/' + newfile._name
                            redimenzionar_imagen(rutacursos, ruta_a_guardar_cursos, 825, 490)
                            curso.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro guardado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})

            elif peticion == 'add_modeloevaluativo':
                try:
                    form = VincularModeloEvaluativoForm(request.POST)
                    if form.is_valid():
                        modelo = form.cleaned_data['modelo']
                        asignar = Curso.objects.get(id=int(request.POST['id']))
                        asignar.modeloevaluativo = modelo
                        asignar.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Modelo asignado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    pass


            elif peticion == 'add_inscrito':
                try:
                    form = InscribirForm(request.POST)
                    if form.is_valid():

                        curso = Curso.objects.get(id=int(request.POST['id']))
                        if not curso.cupo > 0:
                            return JsonResponse(
                                {"respuesta": False, "mensaje": "El curso no cuenta con cupos disponibles"})
                        inscrito = form.cleaned_data['alumno']

                        if not InscritoCurso.objects.filter(status=True, curso=curso, alumno=inscrito).exists():

                            inscrito = InscritoCurso(curso=curso, alumno=inscrito)
                            inscrito.save(request)
                            inscrito.generar_rubros(curso)
                            cuposdisponibles = curso.cupo - 1
                            curso.cupo = cuposdisponibles
                            curso.save(request)
                            return JsonResponse({"respuesta": True, "mensaje": "Alumno inscrito correctamente"})
                        else:
                            return JsonResponse({"respuesta": False, "mensaje": "La persona ya se encuentra inscrita en este curso"})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos"})


            elif peticion == 'edit_curso':
                try:
                    form = CursoForm(request.POST, request.FILES)
                    if form.is_valid():

                        periodo = form.cleaned_data['periodo']
                        docente = form.cleaned_data['docente']
                        nombre = form.cleaned_data['nombre']
                        tiporubro = form.cleaned_data['tiporubro']
                        costo = Decimal(form.cleaned_data['costo'])
                        fechainicio = form.cleaned_data['fechainicio']
                        fechafin = form.cleaned_data['fechafin']
                        fechainicioinscripcion = form.cleaned_data['fechainicioinscripcion']
                        fechafininscripcion = form.cleaned_data['fechafininscripcion']
                        inscripcion = form.cleaned_data['inscripcion']
                        matricula = form.cleaned_data['matricula']
                        horasvirtual = form.cleaned_data['horasvirtual']
                        minasistencia = form.cleaned_data['minasistencia']
                        minnota = form.cleaned_data['minnota']
                        cupo = form.cleaned_data['cupo']
                        observacion = form.cleaned_data['observacion']
                        objetivo = form.cleaned_data['objetivo']
                        contenido = form.cleaned_data['contenido']
                        publicarcurso = form.cleaned_data['publicarcurso']

                        curso = Curso.objects.get(id=int(request.POST['id']))
                        curso.periodo=periodo
                        curso.docente=docente
                        curso.nombre=nombre
                        curso.tiporubro=tiporubro
                        curso.costo=costo
                        curso.fechainicio=fechainicio
                        curso.fechafin=fechafin
                        curso.fechainicioinscripcion=fechainicioinscripcion
                        curso.fechafininscripcion=fechafininscripcion
                        curso.horasvirtual=horasvirtual
                        curso.minasistencia=minasistencia
                        curso.minnota=minnota
                        curso.cupo=cupo
                        curso.observacion=observacion
                        curso.objetivo=objetivo
                        curso.contenido=contenido
                        curso.publicarcurso=publicarcurso
                        curso.save(request)

                        #VERIFICA SI EL CURSO APLICA INSCRIPCIÓN
                        if inscripcion:
                            curso.inscripcion = True
                            if 'tiporubroinscripcion' in request.POST:
                                curso.tiporubroinscripcion = form.cleaned_data['tiporubroinscripcion']

                            if 'costoinscripcion' in request.POST:
                                curso.costoinscripcion = form.cleaned_data['costoinscripcion']

                        # VERIFICA SI EL CURSO APLICA MATRÍCULA
                        if matricula:
                            curso.matricula = True
                            if 'tiporubromatricula' in request.POST:
                                curso.tiporubromatricula = form.cleaned_data['tiporubromatricula']
                            if 'costomatricula' in request.POST:
                                curso.costomatricula = form.cleaned_data['costomatricula']

                        curso.save(request)

                        #GUARDA LA PLANIFICACIÓN DEL CURSO
                        if 'planificacion' in request.FILES:
                            newfile = request.FILES['planificacion']
                            newfile._name = nuevo_nombre("planificacion", newfile._name)
                            curso.planificacion = newfile
                            curso.save(request)

                        #GUARDA LA IMAGEN DEL CURSO QUE SIRVE PARA LA PÁGINA WEB
                        if 'imagenweb' in request.FILES:
                            newfile = request.FILES['imagenweb']
                            newfile._name = nuevo_nombre("imagenweb", newfile._name)
                            curso.fondoweb = newfile
                            curso.save(request)
                            rutaweb = MEDIA_ROOT + '/fondoweb/' + newfile._name
                            ruta_a_guardar_web = MEDIA_ROOT + '/fondoweb/' + newfile._name
                            redimenzionar_imagen(rutaweb, ruta_a_guardar_web, 750, 422)
                            curso.save(request)

                        # GUARDA LA IMAGEN DEL CURSO QUE SIRVE PARA LA PARTE ACADÉMICA
                        if 'imagen' in request.FILES:
                            newfile = request.FILES['imagen']
                            newfile._name = nuevo_nombre("imagen", newfile._name)
                            curso.fondocursos = newfile
                            curso.save(request)
                            rutacursos = MEDIA_ROOT + '/fondocursos/' + newfile._name
                            ruta_a_guardar_cursos = MEDIA_ROOT + '/fondocursos/' + newfile._name
                            redimenzionar_imagen(rutacursos, ruta_a_guardar_cursos, 825, 490)
                            curso.save(request)

                        return JsonResponse({"respuesta": True, "mensaje": "Registro modificado correctamente."})
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": form.errors.items()})
                except Exception as ex:
                    pass

            if peticion == 'eliminar_curso':
                try:
                    with transaction.atomic():
                        registro = Curso.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

            if peticion == 'eliminar_periodo':
                try:
                    with transaction.atomic():
                        registro = Periodo.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

                except Exception as ex:
                    pass

            if peticion == 'eliminar_inscrito':
                try:
                    with transaction.atomic():
                        registro = InscritoCurso.objects.get(pk=request.POST['id'])
                        registro.status = False
                        registro.save(request)
                        rubros = Rubro.objects.filter(status=True, persona=registro.alumno.persona, curso_id=int(request.POST['curso']))
                        idrubros = rubros.values_list('id', flat=True)
                        pagos = Pago.objects.filter(status=True, rubro_id__in=idrubros).update(status=False)
                        if rubros:
                            rubros.update(status=False)
                        return JsonResponse({"respuesta": True, "mensaje": "Inscrito eliminado correctamente."})

                except Exception as ex:
                    pass

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

            elif peticion == 'matricular_alumnos':
                try:
                    curso = Curso.objects.get(id=int(request.POST['id']))
                    periodo = curso.periodo
                    if not PeriodoA.objects.filter(status=True, inicio=periodo.inicio, fin=periodo.fin, activo=True).exists():
                        periodoacademia = PeriodoA(nombre=curso.periodo.nombre, descripcion=curso.periodo.descripcion,
                                                   inicio=curso.periodo.inicio, fin=curso.periodo.fin, activo=curso.periodo.activo)
                        periodoacademia.save(request)
                    else:
                        periodoacademia = PeriodoA.objects.filter(status=True, inicio=periodo.inicio, fin=periodo.fin, activo=True).last()

                    if not curso.migrado:
                        if curso.modeloevaluativo:
                            detallemodelo = DetalleModeloEvaluativo.objects.filter(status=True, modelo=curso.modeloevaluativo)
                            if detallemodelo.exists():
                                modeloevaluativo = curso.modeloevaluativo
                                # if not ModeloEvaluativoA.objects.filter(status=True, nombre=modeloevaluativo.nombre, fecha=modeloevaluativo.fecha, notamaxima=modeloevaluativo.notamaxima, notaaprobar=modeloevaluativo.notaaprobar, asistenciaaprobar=modeloevaluativo.asistenciaaprobar, observaciones=modeloevaluativo.observaciones ).exists():
                                modevalacademia = ModeloEvaluativoA(nombre=modeloevaluativo.nombre, fecha=modeloevaluativo.fecha, notamaxima=modeloevaluativo.notamaxima, notaaprobar=modeloevaluativo.notaaprobar, asistenciaaprobar=modeloevaluativo.asistenciaaprobar, observaciones=modeloevaluativo.observaciones )
                                modevalacademia.save(request)
                                # else:
                                #     modevalacademia = ModeloEvaluativoA.objects.filter(status=True, nombre=modeloevaluativo.nombre,
                                                                        # fecha=modeloevaluativo.fecha,
                                                                        # notamaxima=modeloevaluativo.notamaxima,
                                                                        # notaaprobar=modeloevaluativo.notaaprobar,
                                                                        # asistenciaaprobar=modeloevaluativo.asistenciaaprobar,
                                                                        # observaciones=modeloevaluativo.observaciones).first()
                                cantidadetalle = detallemodelo.count()
                                cantidadetalleA = 0
                                for detalle in detallemodelo:
                                    if DetalleModeloEvaluativoA.objects.filter(status=True, modelo=modevalacademia, nombre=detalle.nombre, notaminima=detalle.notaminima, notamaxima=detalle.notamaxima, orden=detalle.orden).exists():
                                        cantidadetalleA += 1

                                if not cantidadetalle == cantidadetalleA:
                                    for detalle in detallemodelo:
                                        nuevodetalleA = DetalleModeloEvaluativoA(status=True, modelo=modevalacademia,
                                                                                   nombre=detalle.nombre,
                                                                                   notaminima=detalle.notaminima,
                                                                                   notamaxima=detalle.notamaxima,
                                                                                   orden=detalle.orden)
                                        nuevodetalleA.save(request)

                                if not DocenteA.objects.filter(status=True, persona=curso.docente.persona, fechaingreso=curso.docente.fechaingreso, activo=curso.docente.activo).exists():
                                    nuevodocenteA = DocenteA(persona=curso.docente.persona, fechaingreso=curso.docente.fechaingreso, activo=curso.docente.activo)
                                    nuevodocenteA.save(request)
                                else:
                                    nuevodocenteA = DocenteA.objects.filter(status=True, persona=curso.docente.persona, fechaingreso=curso.docente.fechaingreso, activo=curso.docente.activo).first()

                                cursoacademia = CursoA(periodo=periodoacademia, modeloevaluativo=modevalacademia, nombre=curso.nombre,
                                                       estado=2, horasvirtual=curso.horasvirtual, minasistencia=curso.minasistencia,
                                                       minnota=curso.minnota, modalidad=curso.modalidad, docente=nuevodocenteA,
                                                       fechainicio=curso.fechainicio, fechafin=curso.fechafin, observacion=curso.observacion,
                                                       objetivo=curso.objetivo, contenido=curso.contenido, planificacion=curso.planificacion,
                                                       fondoweb=curso.fondoweb, fondocursos=curso.fondocursos, finalizarcurso=curso.finalizarcurso,
                                                       idcursoadministrativo=curso)
                                cursoacademia.save(request)
                                curso.idcursoacademia = cursoacademia
                                curso.migrado = True
                                curso.save(request)
                                inscritos = InscritoCurso.objects.filter(status=True, curso=curso, matriculado=False)
                                nummatriculados = 0
                                for inscrito in inscritos:
                                    if inscrito.puede_matricularse(curso):
                                        nuevoinscritoA = InscritoCursoA(curso=cursoacademia, inscrito=inscrito.alumno.persona)
                                        nuevoinscritoA.save(request)
                                        inscrito.matriculado = True
                                        inscrito.iduseracad_id = nuevoinscritoA.id
                                        inscrito.save(request)
                                        nummatriculados += 1
                                return JsonResponse({"respuesta": True, "mensaje": "Inscritos matriculados correctamente. Total: " + str(nummatriculados) + " matriculados"})

                            else:
                                return JsonResponse({"respuesta": False, "mensaje": "Por favor, ingrese detalle en el modelo evaluativo"})
                        else:
                            return JsonResponse({"respuesta": False, "mensaje": "El curso debe de tener un modelo evaluativo"})
                    else:
                        if curso.idcursoacademia:
                            cursoacademia = CursoA.objects.get(id=curso.idcursoacademia_id)
                            inscritos = InscritoCurso.objects.filter(status=True, curso=curso, matriculado=False)
                            nummatriculados = 0
                            for inscrito in inscritos:
                                if inscrito.puede_matricularse(curso):
                                    nuevoinscritoA = InscritoCursoA(curso=cursoacademia, inscrito=inscrito.alumno.persona)
                                    nuevoinscritoA.save(request)
                                    inscrito.matriculado = True
                                    inscrito.iduseracad_id = nuevoinscritoA.id
                                    inscrito.save(request)
                                    nummatriculados += 1
                            detallemodelo = DetalleModeloEvaluativo.objects.filter(status=True, modelo=curso.modeloevaluativo)
                            if not DetalleModeloEvaluativoA.objects.filter(status=True, modelo=cursoacademia.modeloevaluativo).exists():
                                for detalle in detallemodelo:
                                    nuevodetalleA = DetalleModeloEvaluativoA(status=True, modelo=cursoacademia.modeloevaluativo,
                                                                             nombre=detalle.nombre,
                                                                             notaminima=detalle.notaminima,
                                                                             notamaxima=detalle.notamaxima,
                                                                             orden=detalle.orden)
                                    nuevodetalleA.save(request)
                            return JsonResponse({"respuesta": True, "mensaje": "Inscritos matriculados correctamente. Total: " + str(nummatriculados) + " matriculados"})
                        else:
                            return JsonResponse({"respuesta": False, "mensaje": "Por algún motivo el curso no se encuentra enrolado"})

                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Error al intentar matricular a los alumnos"})

            elif peticion == 'generar_certificado':
                try:
                    data['inscrito'] = inscrito = InscritoCurso.objects.get(id=int(request.POST['id']))
                    firma = '_'
                    longitud_nombre = len(inscrito.curso.docente.__str__())
                    data['firma'] = firma = firma * (longitud_nombre + longitud_nombre + 4)
                    name = "certificado_" + str(inscrito.id)
                    crear_carpeta = os.path.join(os.path.join(ALMACENAMIENTO, 'media', 'certificados'))
                    try:
                        os.makedirs(crear_carpeta)
                    except Exception as ex:
                        pass
                    valida = convertir_html_a_pdf_certificado(
                        'administrativo/inscrito/certificado.html',
                        {'pagesize': 'A4', 'data': data, 'MEDIA_ROOT': MEDIA_ROOT}, name + '.pdf'
                    )
                    if valida:
                        inscrito.certificado = 'certificados/' + name + '.pdf'
                        inscrito.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Certificado generado correctamente."})
                    return JsonResponse({"respuesta": False, "mensaje": "Error al generar el certificado."})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": "Error al generar el certificado."})

        return JsonResponse({"respuesta": False, "mensaje": "Acción incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'add_periodo':
                try:
                    data['titulo'] = 'Agregar nuevo periodo'
                    data['titulo_formulario'] = 'Formulario de registro de periodos'
                    data['peticion'] = 'add_periodo'
                    form = PeriodoForm()
                    data['form'] = form
                    return render(request, "administrativo/periodo/add_periodo.html", data)
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

            if peticion == 'edit_periodo':
                try:
                    data['titulo'] = 'Editar periodo'
                    data['titulo_formulario'] = 'Edición de periodo'
                    data['peticion'] = 'edit_periodo'
                    data['periodo'] = periodo = Periodo.objects.get(pk=request.GET['id'])
                    form = PeriodoForm(initial={
                        'nombre':periodo.nombre,
                        'descripcion': periodo.descripcion,
                        'inicio': periodo.inicio,
                        'fin': periodo.fin,
                        'activo': periodo.activo
                    })
                    data['form'] = form
                    return render(request, "administrativo/periodo/edit_periodo.html", data)
                except Exception as ex:
                    pass
            if peticion == 'edit_curso':
                try:
                    data['titulo'] = 'Editar curso'
                    data['titulo_formulario'] = 'Edición de curso'
                    data['peticion'] = 'edit_curso'
                    data['curso'] = curso = Curso.objects.get(pk=request.GET['id'])
                    form = CursoForm(initial={
                        'periodo':curso.periodo,
                        'docente': curso.docente,
                        'nombre': curso.nombre,
                        'tiporubro': curso.tiporubro,
                        'costo': curso.costo,
                        'fechainicio': curso.fechainicio,
                        'fechafin': curso.fechafin,
                        'fechainicioinscripcion': curso.fechainicioinscripcion,
                        'fechafininscripcion': curso.fechafininscripcion,
                        'inscripcion': curso.inscripcion,
                        'tiporubroinscripcion': curso.tiporubroinscripcion,
                        'costoinscripcion': curso.costoinscripcion,
                        'matricula': curso.matricula,
                        'tiporubromatricula': curso.tiporubromatricula,
                        'costomatricula': curso.costomatricula,
                        'horasvirtual': curso.horasvirtual,
                        'minasistencia': curso.minasistencia,
                        'minnota': curso.minnota,
                        'cupo': curso.cupo,
                        'oferta': curso.oferta,
                        'costooferta': curso.costooferta,
                        'observacion': curso.observacion,
                        'objetivo': curso.objetivo,
                        'contenido': curso.contenido,
                        'publicarcurso': curso.publicarcurso,
                        'planificacion': curso.planificacion,
                        'imagen': curso.fondocursos,
                        'imagenweb': curso.fondoweb,
                    })
                    form.desactivar_campos()
                    form.sin_cuotas()
                    data['form'] = form
                    return render(request, "administrativo/cursos/edit_curso.html", data)
                except Exception as ex:
                    pass

            if peticion == 'generar_certificado':
                try:
                    # data['titulo'] = 'factura'
                    # data['factura'] = factura = Consulta.objects.get(pk=request.GET['id'])

                    return render_pdf_view('docente/certificado_medico.html', data)
                except Exception as ex:
                    pass

            if peticion == 'enviar_factura':

                try:
                    from django.conf import settings
                    from django.core.mail import send_mail
                    factura = Alumno.objects.get(pk=request.GET['id'])
                    mail = create_mail(
                        factura.paciente.persona.email,
                        'Esta es tu factura por la consulta realizada en el centro odontologico',
                        'factura.html',
                        {
                            'factura': factura
                        }
                    )

                    mail.send(fail_silently=False)

                    return JsonResponse({"respuesta": True, "mensaje": "Factura enviado correctamente."})
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))


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

            elif peticion == 'cursos':
                try:
                    data['titulo'] = 'Cursos'
                    data['titulo_tabla'] = 'Lista  de cursos'
                    data['persona_logeado'] = persona_logeado
                    idperiodo = int(request.GET['id'])
                    filtro = (Q(status=True))
                    data['periodo'] = periodo = Periodo.objects.get(id=idperiodo)
                    ruta_paginado = 'peticion=cursos&id=' + str(periodo.id) + '&'
                    if 'var' in request.GET:
                        var = request.GET['var']
                        data['var'] = var
                        filtro = filtro & (Q(nombre__icontains=var) | Q(docente__persona__nombres__icontains=var) |
                                           Q(docente__persona__apellido1__icontains=var) |
                                           Q(docente__persona__cedula__icontains=var))
                        ruta_paginado += "var=" + var + "&"
                    if 'estadocurso' in request.GET:
                        estadocurso = int(request.GET['estadocurso'])
                        if estadocurso > 0:
                            data['estadocurso'] = estadocurso
                            filtro = filtro & (Q(estado=estadocurso))
                            ruta_paginado += "estadocurso=" + str(estadocurso) + "&"
                    lista = Curso.objects.filter(filtro).order_by('id')
                    paginator = Paginator(lista, 25)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['ruta_paginado'] = ruta_paginado
                    data['ESTADO_CURSO'] = ESTADO_CURSO
                    return render(request, "administrativo/cursos/view.html", data)
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

            elif peticion == 'alumnos':
                try:
                    data['titulo'] = 'Alumnos'
                    data['titulo_tabla'] = 'Lista  de Alumnos'
                    data['persona_logeado'] = persona_logeado
                    idperiodo = int(request.GET['id'])
                    data['curso'] = curso = Curso.objects.get(id=idperiodo)
                    ruta_paginado = 'peticion=alumnos&id=' + str(curso.id) + '&'
                    filtro = (Q(status=True) & Q(curso=curso))
                    if 'var' in request.GET:
                        var = request.GET['var']
                        data['var'] = var
                        filtro = filtro & (Q(alumno__persona__nombres__icontains=var) | Q(alumno__persona__apellido1__icontains=var)
                                           | Q(alumno__persona__cedula__icontains=var))
                        ruta_paginado += "var=" + var + "&"
                    if 'estadoinscrito' in request.GET:
                        estadoinscrito = int(request.GET['estadoinscrito'])
                        if estadoinscrito > 0:
                            data['estadoinscrito'] = estadoinscrito
                            filtro = filtro & (Q(estado=estadoinscrito))
                            ruta_paginado += "estadoinscrito=" + str(estadoinscrito) + "&"
                    lista = matriculados = InscritoCurso.objects.filter(filtro).order_by('id')
                    matriculados = matriculados.filter(matriculado=False).count()
                    data['puedematricular'] = True if matriculados > 0 else False
                    paginator = Paginator(lista, 25)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['ruta_paginado'] = ruta_paginado
                    data['ESTADO_INSCRITO'] = ESTADO_INSCRITO
                    return render(request, "administrativo/inscrito/view.html", data)
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

            elif peticion == 'add_inscrito':
                try:
                    data['titulo'] = 'Agregar nuevo inscrito'
                    data['titulo_formulario'] = 'Formulario de inscripción'
                    data['curso'] = Curso.objects.get(id=int(request.GET['id']))
                    data['peticion'] = 'add_inscrito'
                    form = InscribirForm()
                    data['form'] = form
                    return render(request, "administrativo/inscrito/add_inscrito.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            elif peticion == 'add_curso':
                try:
                    data['titulo'] = 'Agregar nuevo curso'
                    data['titulo_formulario'] = 'Formulario de registro de cursos'
                    data['periodo'] = Periodo.objects.get(id=int(request.GET['id']))
                    data['peticion'] = 'add_curso'
                    form = CursoForm()
                    data['form'] = form
                    return render(request, "administrativo/cursos/add_curso.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

            elif peticion == 'add_modeloevaluativo':
                try:
                    data['titulo'] = 'Agregar nuevo modelo a curso'
                    data['titulo_formulario'] = 'Formulario de registro de modelo evaluativo a curso'
                    data['periodo'] = Periodo.objects.get(id=int(request.GET['idperiodo']))
                    data['curso'] = Curso.objects.get(id=int(request.GET['id']))
                    data['peticion'] = 'add_modeloevaluativo'
                    form = VincularModeloEvaluativoForm()
                    data['form'] = form
                    return render(request, "administrativo/cursos/add_modeloevaluativo.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass


        else:
            try:
                data['titulo'] = 'Periodos'
                data['titulo_tabla'] = 'Lista  de periodos'
                data['persona_logeado'] = persona_logeado
                filtro = (Q(status=True))
                ruta_paginado = request.path
                if 'var' in request.GET:
                    var = request.GET['var']
                    data['var'] = var
                    filtro = filtro & (Q(nombre__icontains=var) |
                                       Q(descripcion__icontains=var))
                    ruta_paginado += "?var=" + var + "&"
                lista = Periodo.objects.filter(filtro).order_by('id')
                paginator = Paginator(lista, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/periodo/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
