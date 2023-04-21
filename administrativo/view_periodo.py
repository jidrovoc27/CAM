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
                       return JsonResponse(  {"respuesta": False, "mensaje": "Ha ocurrido un error al enviar los datos."})


                except Exception as ex:
                   transaction.set_rollback(True)
                   return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente mas tarde."})

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


                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"respuesta": False, "mensaje": "Ha ocurrido un error, intente mas tarde."})

            if peticion == 'eliminar_alumno':
                try:
                    with transaction.atomic():
                        registro = Alumno.objects.get(pk=request.POST['id'])
                        persona = Persona.objects.get(pk=registro.persona_id)
                        persona.status = False
                        persona.save()
                        registro.status = False
                        registro.save(request)
                        return JsonResponse({"respuesta": True, "mensaje": "Registro eliminado correctamente."})

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
        return JsonResponse({"respuesta": False, "mensaje": "acción Incorrecta."})
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
                    paginator = Paginator(lista, 15)
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
                    data['periodo'] = periodo = Periodo.objects.get(id=idperiodo)
                    lista = Curso.objects.filter(status=True, periodo=periodo).order_by('id')
                    paginator = Paginator(lista, 15)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    return render(request, "administrativo/cursos/view.html", data)
                except Exception as ex:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

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


        else:
            try:
                data['titulo'] = 'Periodos'
                data['titulo_tabla'] = 'Lista  de periodos'
                data['persona_logeado'] = persona_logeado
                lista = Periodo.objects.filter(status=True).order_by('id')
                paginator = Paginator(lista, 15)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                return render(request, "administrativo/periodo/view.html", data)
            except Exception as ex:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
