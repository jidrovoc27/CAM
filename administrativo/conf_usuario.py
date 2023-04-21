import sys
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from administrativo.funciones import add_data_aplication
from administrativo.models import Persona


@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_usuario(request):
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
                data['titulo'] = 'Configuración de usuarios'
                data['persona_logeado'] = persona_logeado
                return render(request, "conf_sistema/view_usuario.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
