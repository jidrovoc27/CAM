import sys
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from datetime import *

from administrativo.forms import ConsultaForm, PagoForm, FacturaForm
from administrativo.funciones import add_data_aplication
from administrativo.models import *
from django.db.models import Sum
from django.template.loader import get_template


def view_pagina(request):
    global ex
    data = {}

    if request.method == 'POST':
        if 'peticion' in request.POST:
            peticion = request.POST['peticion']

        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
    else:
        if 'peticion' in request.GET:
            peticion = request.GET['peticion']

            if peticion == 'detallecurso':
                try:
                    data['curso'] = curso = Curso.objects.get(pk=request.GET['id'])
                    data['cuotas'] = cuotas = CuotasCurso.objects.filter(curso=curso)
                    template = get_template("paginaweb/detallecurso.html")
                    return JsonResponse({"respuesta": True, 'data': template.render(data)})
                except Exception as ex:
                    pass


        else:
            pass
