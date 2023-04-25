from django.db import models
import datetime
from datetime import datetime
from decimal import Decimal
from django.forms import model_to_dict

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

def add_data_aplication(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil
    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    if 'persona' not in request.session:
        usuariologeado = request.user
        personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
        # data['personalogeada'] = personalogeada[0]
        if personalogeada:
            request.session['persona'] = model_to_dict(personalogeada.first())
        else:
            persona_logeada = 'CAM'
            request.session['persona'] = 'CAM'
        # request.session.save()

    if 'perfil_principal' not in request.session:
        if not request.session['persona'] == 'CAM':
            mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
            tipoperfil = mis_perfiles.first()
            if tipoperfil.is_administrador == True:
                request.session['tipoperfil'] = 1
            elif tipoperfil.is_profesor == True:
                request.session['tipoperfil'] = 2
            elif tipoperfil.is_alumno == True:
                request.session['tipoperfil'] = 3
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

def act_data_aplication(request,data):
    from administrativo.models import Modulo, Persona, PersonaPerfil

    del request.session['lista_url_ruta']
    del request.session['persona']
    del request.session['perfil_principal']
    del request.session['tipoperfil']


    if 'lista_url_ruta' not in request.session:
        request.session['lista_url_ruta'] = [['/', 'Inicio']]
    lista_url_ruta = request.session['lista_url_ruta']
    if 'persona' not in request.session:
        usuariologeado = request.user
        personalogeada = Persona.objects.filter(usuario=usuariologeado, status=True)
        data['personalogeada'] = personalogeada[0]
        if personalogeada:
            request.session['persona'] = model_to_dict(personalogeada.first())
        else:
            persona_logeada = 'CAM'
            request.session['persona'] = 'CAM'
        # request.session.save()

    if 'perfil_principal' not in request.session:
        if not request.session['persona'] == 'CAM':
            mis_perfiles = PersonaPerfil.objects.filter(status=True, persona=request.user.persona_set.filter(status=True).first())
            tipoperfil = mis_perfiles.first()
            if data['tipoperfil'] == 'is_administrador':
                request.session['tipoperfil'] = 1
            elif data['tipoperfil'] == 'is_profesor':
                request.session['tipoperfil'] = 2
            elif data['tipoperfil'] == 'is_alumno':
                request.session['tipoperfil'] = 3
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
