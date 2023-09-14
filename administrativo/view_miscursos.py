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
def view_miscursos(request):
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

            if peticion == 'migrar_calificaciones':
                try:
                    curso = Curso.objects.get(id=int(request.POST['id']))
                    cursoacad = CursoA.objects.get(id=curso.idcursoacademia_id)
                    modeloevaluativo = cursoacad.modeloevaluativo
                    detallemodeloacad = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=modeloevaluativo)
                    inscritoacad = InscritoCursoA.objects.filter(status=True, curso=cursoacad)
                    resultado = 0
                    if detallemodeloacad:
                        for inscrito in inscritoacad:
                            for deta in detallemodeloacad:
                                filtro = (Q(status=True) & Q(inscrito=inscrito))
                                detalleadm = DetalleModeloEvaluativo.objects.filter(status=True, nombre=deta.nombre, modelo=curso.modeloevaluativo)

                                #CONSULTA TODAS LAS ACTIVIDADES ENTREGADAS
                                detalleactividad = lista_actividades = conteoact = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=deta)
                                lista_actividades = lista_actividades.values_list('id')

                                #CONSULTA TODOS LOS CUESTIONARIOS REALIZADOS
                                detalleexamenes = lista_examenes = conteoexam = Examen.objects.filter(status=True, activo=True, detalle=deta)
                                lista_examenes = lista_examenes.values_list('id')

                                #TOTAL DE CUESTIONARIOS Y ACTIVIDADES
                                conteoexam = conteoexam.count()
                                conteoact = conteoact.count()

                                #SUMA DEL TOTAL DE CUESTIONARIOS Y ACTIVIDADES
                                conteo = conteoact + conteoexam

                                #CONSULTA TODAS AQUELLAS ACTIVIDADES O CUESTIONARIOS QUE CUENTEN CON NOTA
                                filtro = filtro & (Q(actividad_id__in=lista_actividades) | Q(examen_id__in=lista_examenes))
                                totalnotas = NotaInscritoActividadA.objects.filter(filtro).aggregate(total=Sum('nota'))
                                totalnotas = totalnotas['total'] if totalnotas['total'] else 0


                                if conteo > 0 and totalnotas:
                                    resultado = totalnotas / conteo
                                else:
                                    resultado = 0
                                if detalleadm:
                                    inscritoadm = InscritoCurso.objects.filter(iduseracad_id=inscrito.id, curso=curso)
                                    if inscritoadm:
                                        notaadm = NotaInscrito.objects.filter(status=True, inscrito=inscritoadm.first(), modelo=detalleadm.first())
                                        if notaadm:
                                            notaadm = notaadm.first()
                                            notaadm.notafinal = resultado
                                            notaadm.save(request)
                                        else:
                                            notaadm = NotaInscrito(inscrito=inscritoadm.first(), modelo=detalleadm.first(), notafinal = resultado)
                                            notaadm.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Calificaciones migradas correctamente"})
                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

            if peticion == 'finalizar_curso':
                try:
                    curso = Curso.objects.get(id=int(request.POST['id']))
                    inscritos = InscritoCurso.objects.filter(status=True, curso=curso)
                    for inscrito in inscritos:
                        promediofinal = solo_2_decimales(inscrito.calcularpromedio(curso.id), 2)
                        if promediofinal >= curso.minnota:
                            inscrito.estado = 1
                        else:
                            inscrito.estado = 2
                        inscrito.notafinal = promediofinal
                        inscrito.save(request)
                    curso.estado = 3
                    curso.finalizarcurso = True
                    curso.save(request)
                    cursoacad = CursoA.objects.get(id=curso.idcursoacademia_id)
                    cursoacad.estado = 3
                    cursoacad.finalizarcurso = True
                    cursoacad.save(request)
                    return JsonResponse({"respuesta": True, "mensaje": "Curso finalizado correctamente"})
                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente más tarde."})

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']

            if peticion == 'veralumnos':
                try:
                    data['titulo'] = 'Alumnos'
                    data['titulo_tabla'] = 'Alumnos matriculados'
                    data['persona_logeado'] = persona_logeado
                    data['curso'] = curso = Curso.objects.get(id=int(request.GET['id']))
                    ruta_paginado = 'peticion=veralumnos&id=' + str(curso.id) + '&'
                    filtro = (Q(status=True) & Q(curso=curso))
                    if 'var' in request.GET:
                        var = request.GET['var']
                        data['var'] = var
                        filtro = filtro & (Q(alumno__persona__nombres__icontains=var) |
                                           Q(alumno__persona__apellidos__icontains=var) |
                                           Q(alumno__persona__cedula__icontains=var))
                        ruta_paginado += "var=" + var + "&"
                    lista = InscritoCurso.objects.filter(filtro).order_by('id')
                    paginator = Paginator(lista, 25)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['ruta_paginado'] = ruta_paginado
                    return render(request, "administrativo/miscursos/misalumnos.html", data)
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass

        else:
            try:
                data['titulo'] = 'Mis cursos'
                data['titulo_tabla'] = 'Lista  de cursos a cargo'
                data['persona_logeado'] = persona_logeado
                filtro = (Q(status=True) & Q(docente__persona=persona_logeado) & Q(migrado=True))
                ruta_paginado = request.path
                if 'var' in request.GET:
                    var = request.GET['var']
                    data['var'] = var
                    filtro = filtro & (Q(nombre__icontains=var))
                    ruta_paginado += "?var=" + var + "&"
                lista = Curso.objects.filter(filtro).order_by('id')
                paginator = Paginator(lista, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/miscursos/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
