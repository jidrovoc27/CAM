from django.db import models
import os
from CAM import settings
from django.contrib.staticfiles import finders
from django.http import JsonResponse, HttpResponse
from CAM.settings import BASE_DIR, ALMACENAMIENTO
import datetime
from datetime import datetime
from decimal import Decimal
from django.forms import model_to_dict
from django.contrib.auth.models import User, Group
from django.template.loader import get_template
# from io import StringIO
import io as StringIO
from xhtml2pdf import pisa
import uuid

def convertir_html_a_pdf_certificado(template_src, context_dict, filename):
    template = get_template(template_src)
    html = template.render(context_dict).encode(encoding="UTF-8")
    result = StringIO.BytesIO()
    output_folder = os.path.join(ALMACENAMIENTO, 'media', 'certificados')
    filepdf = open(output_folder + os.sep + filename, "w+b")
    links = lambda uri, rel: os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
    pdf1 = pisa.pisaDocument(StringIO.BytesIO(html), dest=filepdf, link_callback=links)
    pisaStatus = pisa.CreatePDF(StringIO.BytesIO(html), result, link_callback=links)
    if not pdf1.err:
        # return HttpResponse(result.getvalue(), content_type='application/pdf')
        return True
    return JsonResponse({"result": "bad", "mensaje": u"Incidencias al generar el certificado"})

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

def solo_2_decimales(valor, decimales=None):
    if valor:
        if decimales:
            if decimales > 0:
                return float(Decimal(valor if valor else 0).quantize(
                    Decimal('.' + ''.zfill(decimales - 1) + '1')) if valor else 0)
            else:
                return float(Decimal(valor if valor else 0).quantize(Decimal('0')))
    return valor if valor else 0

def quitar_caracteres(cadena):
    return cadena.replace(u'ñ', u'n').replace(u'Ñ', u'N').replace(u'Á', u'A').replace(u'á', u'a').replace(u'É',u'E').replace(u'é', u'e').replace(u'Í', u'I').replace(u'í', u'i').replace(u'Ó', u'O').replace(u'ó', u'o').replace(u'Ú',u'U').replace(u'ú', u'u')

def nuevo_nombre(nombre, original):
    nombre = quitar_caracteres(nombre).lower().replace(' ', '_')
    ext = ""
    if original.find(".") > 0:
        ext = original[original.rfind("."):]
    fecha = datetime.now().date()
    hora = datetime.now().time()
    return nombre + fecha.year.__str__() + fecha.month.__str__() + fecha.day.__str__() + hora.hour.__str__() + hora.minute.__str__() + hora.second.__str__() + ext.lower()


class ModeloBase(models.Model):
    from django.contrib.auth.models import User
    usuario_creacion = models.ForeignKey(User, verbose_name='Usuario Creación', blank=True, null=True, on_delete= models.CASCADE, related_name='+', editable=False)
    fecha_creacion = models.DateTimeField(verbose_name='Fecha creación',auto_now_add=True)
    fecha_modificacion = models.DateTimeField(verbose_name='Fecha Modificación', auto_now=True)
    usuario_modificacion = models.ForeignKey(User, verbose_name='Usuario Modificación', blank=True, null=True, on_delete= models.CASCADE, related_name='+', editable=False)
    status = models.BooleanField(verbose_name="Estado del registro", default=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        usuario = None
        if len(args):
            usuario = args[0].user.id
        if self.id:
            self.usuario_modificacion_id = usuario
        else:
            self.usuario_creacion_id = usuario
        models.Model.save(self)

class ModelBaseChat(models.Model):
	id = models.UUIDField(default=uuid.uuid4, primary_key=True, db_index=True, editable=False)
	tiempo = models.DateTimeField(auto_now_add=True, blank=True, null=True)
	actualizar = models.DateTimeField(auto_now=True, blank=True, null=True)

	class Meta:
		abstract = True

def add_data_aplication(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil
    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    # if 'persona' not in request.session:
    #     usuariologeado = request.user
    #     personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
    #     # data['personalogeada'] = personalogeada[0]
    #     if personalogeada:
    #         request.session['persona'] = model_to_dict(personalogeada.first())
    #     else:
    #         persona_logeada = 'CAM'
    #         request.session['persona'] = 'CAM'
        # request.session.save()

    if 'perfil_principal' not in request.session:
        # if not request.session['persona'] == 'CAM':
        mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
        if mis_perfiles:
            tipoperfil = mis_perfiles.first()
            if tipoperfil.is_administrador == True:
                grupo_administrativo = Group.objects.filter(name='Administrativo')
                if grupo_administrativo:
                    request.session['tipoperfil'] = grupo_administrativo.first().id
            elif tipoperfil.is_profesor == True:
                grupo_profesor = Group.objects.filter(name='Docente')
                if grupo_profesor:
                    request.session['tipoperfil'] = grupo_profesor.first().id
            elif tipoperfil.is_alumno == True:
                grupo_alumno = Group.objects.filter(name='Alumno')
                if grupo_alumno:
                    request.session['tipoperfil'] = grupo_alumno.first().id
            request.session['perfil_principal'] = model_to_dict(mis_perfiles.first())
        # request.session.save()

    if request.method == 'GET' and request.path:
        if Modulo.objects.values("id").filter(ruta=request.path[1:],status=True).exists():
            modulo = Modulo.objects.values("ruta", "nombre").filter(status=True,ruta=request.path[1:])[0]
            ruta = ['/' + modulo['ruta'], modulo['nombre']]
            if lista_url_ruta.count(ruta) <= 0:
                if lista_url_ruta.__len__() >= 7:
                    last_ruta = lista_url_ruta[1]
                    lista_url_ruta.remove(last_ruta)
                    lista_url_ruta.append(ruta)
                else:
                    lista_url_ruta.append(ruta)
            request.session['lista_url_ruta'] = lista_url_ruta
        else:
            pass
    data["lista_url_ruta"] = lista_url_ruta

def add_data_aplication_academia(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil
    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    # if 'persona' not in request.session:
    #     usuariologeado = request.user
    #     personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
    #     # data['personalogeada'] = personalogeada[0]
    #     if personalogeada:
    #         request.session['persona'] = model_to_dict(personalogeada.first())
    #     else:
    #         persona_logeada = 'CAM'
    #         request.session['persona'] = 'CAM'
        # request.session.save()
    # if not request.session['persona'] == 'CAM':
    mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
    tipoperfil = mis_perfiles.first()

    if 'perfil_principal' not in request.session:
            # if tipoperfil.is_administrador == True:
            #     grupo_administrativo = Group.objects.filter(name='Administrativo')
            #     if grupo_administrativo:
            #         request.session['tipoperfil'] = grupo_administrativo.first().id
            if tipoperfil.is_alumno == True:
                grupo_alumno = Group.objects.filter(name='Alumno')
                if grupo_alumno:
                    request.session['tipoperfil'] = grupo_alumno.first().id
            elif tipoperfil.is_profesor == True:
                grupo_profesor = Group.objects.filter(name='Docente')
                if grupo_profesor:
                    request.session['tipoperfil'] = grupo_profesor.first().id

            request.session['perfil_principal'] = model_to_dict(mis_perfiles.first())
        # request.session.save()

    if 'identificadorperfil' not in request.session:
        if tipoperfil.is_alumno == True:
            request.session['identificadorperfil'] = 'is_alumno'
        elif tipoperfil.is_profesor == True:
            request.session['identificadorperfil'] = 'is_profesor'


    if request.method == 'GET' and request.path:
        if Modulo.objects.values("id").filter(ruta=request.path[1:],status=True).exists():
            modulo = Modulo.objects.values("ruta", "nombre").filter(status=True,ruta=request.path[1:])[0]
            ruta = ['/' + modulo['ruta'], modulo['nombre']]
            if lista_url_ruta.count(ruta) <= 0:
                if lista_url_ruta.__len__() >= 7:
                    last_ruta = lista_url_ruta[1]
                    lista_url_ruta.remove(last_ruta)
                    lista_url_ruta.append(ruta)
                else:
                    lista_url_ruta.append(ruta)
            request.session['lista_url_ruta'] = lista_url_ruta
        else:
            pass
    data["lista_url_ruta"] = lista_url_ruta

def act_data_aplication(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil

    del request.session['lista_url_ruta']
    # del request.session['persona']
    del request.session['perfil_principal']
    del request.session['tipoperfil']


    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    # if 'persona' not in request.session:
    #     usuariologeado = request.user
    #     personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
    #     data['personalogeada'] = personalogeada[0]
    #     if personalogeada:
    #         request.session['persona'] = model_to_dict(personalogeada.first())
    #     else:
    #         persona_logeada = 'CAM'
    #         request.session['persona'] = 'CAM'
        # request.session.save()

    if 'perfil_principal' not in request.session:
        # if not request.session['persona'] == 'CAM':
        mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
        tipoperfil = mis_perfiles.first()
        if data['tipoperfil'] == 'is_administrador':
            grupo_administrativo = Group.objects.filter(name='Administrativo')
            if grupo_administrativo:
                request.session['tipoperfil'] = grupo_administrativo.first().id
        elif data['tipoperfil'] == 'is_profesor':
            grupo_profesor = Group.objects.filter(name='Docente')
            if grupo_profesor:
                request.session['tipoperfil'] = grupo_profesor.first().id
        elif data['tipoperfil'] == 'is_alumno':
            grupo_alumno = Group.objects.filter(name='Alumno')
            if grupo_alumno:
                request.session['tipoperfil'] = grupo_alumno.first().id
        request.session['perfil_principal'] = model_to_dict(mis_perfiles.first())
        # request.session.save()

    if request.method == 'GET' and request.path:
        if Modulo.objects.values("id").filter(ruta=request.path[1:],status=True).exists():
            modulo = Modulo.objects.values("ruta", "nombre").filter(status=True,ruta=request.path[1:])[0]
            ruta = ['/' + modulo['ruta'], modulo['nombre']]
            if lista_url_ruta.count(ruta) <= 0:
                if lista_url_ruta.__len__() >= 7:
                    last_ruta = lista_url_ruta[1]
                    lista_url_ruta.remove(last_ruta)
                    lista_url_ruta.append(ruta)
                else:
                    lista_url_ruta.append(ruta)
            request.session['lista_url_ruta'] = lista_url_ruta
        else:
            pass
    data["lista_url_ruta"] = lista_url_ruta

def act_data_aplication_academia(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil

    del request.session['lista_url_ruta']
    # del request.session['persona']
    del request.session['perfil_principal']
    del request.session['tipoperfil']
    del request.session['identificadorperfil']

    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    # if 'persona' not in request.session:
    #     usuariologeado = request.user
    #     personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
    #     data['personalogeada'] = personalogeada[0]
    #     if personalogeada:
    #         request.session['persona'] = model_to_dict(personalogeada.first())
    #     else:
    #         persona_logeada = 'CAM'
    #         request.session['persona'] = 'CAM'
        # request.session.save()

    if 'perfil_principal' not in request.session:
        # if not request.session['persona'] == 'CAM':
        mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
        tipoperfil = mis_perfiles.first()
        # if data['tipoperfil'] == 'is_administrador':
        #     grupo_administrativo = Group.objects.filter(name='Administrativo')
        #     if grupo_administrativo:
        #         request.session['tipoperfil'] = grupo_administrativo.first().id
        if data['tipoperfil'] == 'is_alumno':
            request.session['identificadorperfil'] = data['tipoperfil']
            grupo_alumno = Group.objects.filter(name='Alumno')
            if grupo_alumno:
                request.session['tipoperfil'] = grupo_alumno.first().id
        elif data['tipoperfil'] == 'is_profesor':
            request.session['identificadorperfil'] = data['tipoperfil']
            grupo_profesor = Group.objects.filter(name='Docente')
            if grupo_profesor:
                request.session['tipoperfil'] = grupo_profesor.first().id

        request.session['perfil_principal'] = model_to_dict(mis_perfiles.first())
        # request.session.save()


    if request.method == 'GET' and request.path:
        if Modulo.objects.values("id").filter(ruta=request.path[1:],status=True).exists():
            modulo = Modulo.objects.values("ruta", "nombre").filter(status=True,ruta=request.path[1:])[0]
            ruta = ['/' + modulo['ruta'], modulo['nombre']]
            if lista_url_ruta.count(ruta) <= 0:
                if lista_url_ruta.__len__() >= 7:
                    last_ruta = lista_url_ruta[1]
                    lista_url_ruta.remove(last_ruta)
                    lista_url_ruta.append(ruta)
                else:
                    lista_url_ruta.append(ruta)
            request.session['lista_url_ruta'] = lista_url_ruta
        else:
            pass
    data["lista_url_ruta"] = lista_url_ruta

def conviert_html_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict).encode(encoding="UTF-8")
    result = StringIO.BytesIO()
    pisaStatus = pisa.CreatePDF(StringIO.BytesIO(html), result, link_callback=link_callback)
    if not pisaStatus.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return JsonResponse({"result": "bad", "mensaje": u"Problemas al ejecutar el reporte."})

def generar_nombre(nombre, original):
    nombre = quitar_caracteres(nombre).lower().replace(' ', '_')
    ext = ""
    if original.find(".") > 0:
        ext = original[original.rfind("."):]
    fecha = datetime.now().date()
    hora = datetime.now().time()
    return nombre + fecha.year.__str__() + fecha.month.__str__() + fecha.day.__str__() + hora.hour.__str__() + hora.minute.__str__() + hora.second.__str__() + ext.lower()

def customgetattr(object, name):
    r = getattr(object, name)
    if str(type(r)) == "<class 'method'>" or str(type(r)) == "<class 'function'>":
        return r()
    return r

def remover_caracteres_tildes_unicode(cadena):
    return cadena.replace(u'Á', u'A').replace(u'á', u'a').replace(u'É', u'E').replace(u'é', u'e').replace(u'Í',
                                                                                                          u'I').replace(
        u'í', u'i').replace(u'Ó', u'O').replace(u'ó', u'o').replace(u'Ú', u'U').replace(u'ú', u'u')
