import sys
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from administrativo.funciones import add_data_aplication
from administrativo.models import Persona


@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_persona(request):
    global ex
    data = {}
    add_data_aplication(request, data)
    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

            if peticion == 'eliminar_persona':
                try:
                    if request.user.is_superuser:
                        persona_delete = Persona.objects.get(id=int(request.POST['id']))
                        persona_delete.status = False
                        persona_delete.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Persona eliminado correctamente."})
                except Exception as ex:
                    return JsonResponse({"respuesta": False, "mensaje": 'Error al eliminar a la persona.'})

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
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
