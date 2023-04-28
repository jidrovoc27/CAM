import os
import sys
from io import StringIO
import datetime
from datetime import *
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

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_lead(request):
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


        else:
            try:
                data['titulo'] = 'Leads'
                data['titulo_tabla'] = 'Lista  de interesados'
                data['persona_logeado'] = persona_logeado
                lista = Lead.objects.filter(status=True).order_by('id')
                paginator = Paginator(lista, 15)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/lead/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
