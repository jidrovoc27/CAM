import sys
import datetime
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from administrativo.funciones import add_data_aplication
from administrativo.models import Persona, PersonaPerfil, Docente, Alumno


@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_persona(request):
    global ex
    data = {}
    add_data_aplication(request, data)
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

            if peticion == 'crear_perfil':
                try:
                    tipo = request.POST['tipo']
                    idpersona = request.POST['id']
                    filtro = (Q(status=True) & Q(persona_id=idpersona))

                    if tipo == 'Administrativo':
                        filtro = filtro & Q(is_administrador=True)
                    elif tipo == 'Docente':
                        filtro = filtro & Q(is_profesor=True)
                    elif tipo == 'Alumno':
                        filtro = filtro & Q(is_alumno=True)
                    perfil_ = PersonaPerfil.objects.filter(filtro)
                    if not perfil_.exists():
                        newperfil = PersonaPerfil(persona_id=idpersona)
                        newperfil.save(request)
                        if tipo == 'Administrativo':
                            newperfil.is_administrador = True
                            newperfil.save(request)
                        elif tipo == 'Docente':
                            newperfil.is_profesor = True
                            newperfil.save(request)
                        elif tipo == 'Alumno':
                            newperfil.is_alumno = True
                            newperfil.save(request)
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": 'La persona ya cuenta con perfil'})



                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": 'Error al crear el perfil a la persona'})

            elif peticion == 'activar_perfil':
                try:
                    tipo = request.POST['tipo']
                    idpersona = request.POST['id']
                    filtro = (Q(status=True) & Q(persona_id=idpersona))
                    perfil_ = PersonaPerfil.objects.filter(filtro)

                    if perfil_.exists():
                        perfil_ = perfil_.first()
                        perfil_.status = True
                        perfil_.save(request)
                        if tipo == 'Administrativo':
                            perfil_.is_administrador = True
                            perfil_.save(request)
                        elif tipo == 'Docente':
                            perfil_.is_profesor = True
                            perfil_.save(request)
                            consultar_docente = Docente.objects.filter(status=True, persona_id=idpersona)
                            if not consultar_docente.exists():
                               crear_docente = Docente(persona_id=idpersona, fechaingreso=datetime.now().date())
                               crear_docente.save(request)
                        elif tipo == 'Alumno':
                            perfil_.is_alumno = True
                            perfil_.save(request)
                            consultar_alumno = Alumno.objects.filter(status=True, persona_id=idpersona)
                            if not consultar_alumno.exists():
                                crear_alumno = Alumno(persona_id=idpersona)
                                crear_alumno.save(request)
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": 'La persona no cuenta con perfil'})

                    return JsonResponse({"respuesta": True, "mensaje": 'Perfil activado correctamente'})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": 'Error al crear el perfil a la persona'})

            elif peticion == 'desactivar_perfil':
                try:
                    tipo = request.POST['tipo']
                    idpersona = int(request.POST['id'])
                    filtro = (Q(status=True) & Q(persona_id=idpersona))
                    perfil_ = PersonaPerfil.objects.filter(filtro)

                    if perfil_.exists():
                        perfil_ = perfil_.first()
                        if tipo == 'Administrativo':
                            perfil_.is_administrador = False
                            perfil_.save(request)
                        elif tipo == 'Docente':
                            perfil_.is_profesor = False
                            perfil_.save(request)
                        elif tipo == 'Alumno':
                            perfil_.is_alumno = False
                            perfil_.save(request)
                    else:
                        return JsonResponse({"respuesta": False, "mensaje": 'La persona no cuenta con perfil'})

                    return JsonResponse({"respuesta": True, "mensaje": 'Perfil desactivado correctamente'})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": 'Error al desactivar el perfil a la persona'})

            elif peticion == 'eliminar_persona':
                try:
                    if request.user.is_superuser:
                        persona_delete = Persona.objects.get(id=int(request.POST['id']))
                        persona_delete.status = False
                        persona_delete.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Persona eliminado correctamente"})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": 'Error al eliminar a la persona'})

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta"})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']
            if peticion == 'peticion':
                try:
                    pass
                except Exception as ex:
                    transaction.set_rollback(True)
                    pass
        else:
            try:
                data['titulo'] = 'Configuración de personas'
                personas = Persona.objects.filter(status=True)
                paginator = Paginator(personas, 25)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "conf_sistema/view_persona.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
