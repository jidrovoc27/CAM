from datetime import datetime
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.forms import DateTimeInput, ModelChoiceField

from administrativo.models import *


class ExtFileField(forms.FileField):
    """
    * max_upload_size - a number indicating the maximum file size allowed for upload.
            500Kb - 524288
            1MB - 1048576
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    t = ExtFileField(ext_whitelist=(".pdf", ".txt"), max_upload_size=)
    """

    def __init__(self, *args, **kwargs):
        ext_whitelist = kwargs.pop("ext_whitelist")
        self.ext_whitelist = [i.lower() for i in ext_whitelist]
        self.max_upload_size = kwargs.pop("max_upload_size")
        super(ExtFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        upload = super(ExtFileField, self).clean(*args, **kwargs)
        if upload:
            size = upload.size
            filename = upload.name
            ext = os.path.splitext(filename)[1]
            ext = ext.lower()
            if size == 0 or ext not in self.ext_whitelist or size > self.max_upload_size:
                raise forms.ValidationError("Tipo de fichero o tamanno no permitido!")

def deshabilitar_campo(form, campo):
    form.fields[campo].widget.attrs['readonly'] = True
    form.fields[campo].widget.attrs['disabled'] = True


def campo_requerido(form, campo):
    form.fields[campo].widget.attrs['required'] = True


def campo_no_requerido(form, campo):
    form.fields[campo].widget.attrs['required'] = False


def habilitar_campo(form, campo):
    form.fields[campo].widget.attrs['readonly'] = False
    form.fields[campo].widget.attrs['disabled'] = False


def campo_solo_lectura(form, campo):
    form.fields[campo].widget.attrs['readonly'] = True


class RegistroUsuarioForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(RegistroUsuarioForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            self.fields['password1'].widget.attrs['class'] = "form-control"
            self.fields['password2'].widget.attrs['class'] = "form-control"

    email = forms.EmailField(label="Email", widget=forms.TextInput(attrs={'class': 'form-control', }))
    nombre1 = forms.CharField(label="1er. Nombre", widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    nombre2 = forms.CharField(label="2do. Nombre", widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    apellido1 = forms.CharField(label="Apellido paterno", widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    apellido2 = forms.CharField(label="Apellido materno", widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress' : 'return solo_letras(event)',}))
    cedula = forms.CharField(label=u"Cédula", max_length=10, required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_numeros(event)',}))
    genero = forms.ModelChoiceField(label=u"Género", queryset=Genero.objects.filter(status=True),
                                    widget=forms.Select(attrs={'class': 'form-control', }))
    telefono_movil = forms.CharField(label=u"Teléfono móvil", max_length=50, help_text="Ingrese su número de telefono sin el 0",
                                     widget=forms.TextInput(attrs={'class': 'form-control', }))
    telefono_convencional = forms.CharField(label=u"Teléfono Convencional", max_length=50, required=False,
                                            widget=forms.TextInput(attrs={'class': 'form-control', }))


    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        r = User.objects.filter(username=username)
        if r.count():
            raise ValidationError("Nombre de usuario ya existe.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        r = User.objects.filter(email=email)
        if r.count():
            raise ValidationError("Email ya existe")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("La contraseña no coincide.")

        return password2

    class Meta:
        model = User
        fields = ("username", "email",)

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',

                }
            ),
        }

class ModuloForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    descripcion = forms.CharField(label='Descripción', required=True,
                                  widget=forms.TextInput(attrs={'class': ' form-control ','onKeyPress' : 'return solo_letras(event)', }))
    ruta = forms.CharField(label='Ruta', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    icono = forms.ImageField(label='Icono', required=False, widget=forms.ClearableFileInput(
        attrs={'class': 'dropify', 'data-allowed-file-extensions': 'PNG png'}))
    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(
        attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))

    def add(self):
        campo_requerido(self, 'icono')

    def editar(self):
        campo_no_requerido(self, 'icono')


class PersonaForm(forms.Form):
    nombres = forms.CharField(label='Nombres', required=True,
                             widget=forms.TextInput(attrs={'class': ' form-control','onKeyPress' : 'return solo_letras(event)',  }))
    # nombre2 = forms.CharField(label='2ª Nombre', required=True,
    #                          widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)',  }))
    apellidos = forms.CharField(label='Apellidos', required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    # apellido2 = forms.CharField(label='2º Apellido', required=True,
    #                          widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)',  }))
    email = forms.CharField(label="Correo electrónico", max_length=200, required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control',}))
    cedula = forms.CharField(label="Cédula", max_length=10, required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_numeros(event)',}))
    genero = forms.ModelChoiceField(label="Género",required=True, queryset=Genero.objects.filter(status=True),
                                  widget=forms.Select(attrs={'class': 'form-control',}))

    telefono_movil = forms.CharField(label="Teléfono móvil", max_length=50, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'(99 123 1234)'}))
    telefono_convencional = forms.CharField(label=u"Teléfono fijo", max_length=50, required=False,
                                    widget=forms.TextInput(attrs={'class': 'form-control ',}))
    ciudad = forms.CharField(label=u"Ciudad", max_length=50, required=False,
                                     widget=forms.TextInput(
                                         attrs={'class': 'form-control', 'placeholder': 'Milagro'}))
    direccion = forms.CharField(label=u"Dirección", required=False,
                                     widget=forms.TextInput(
                                         attrs={'class': 'form-control', 'placeholder': 'Av. Quito'}))
    referencia = forms.CharField(label=u"Referencia", max_length=50, required=False,
                                     widget=forms.TextInput(
                                         attrs={'class': 'form-control', 'placeholder': 'A 2 cuadras..'}))


    def editar(self):
        campo_solo_lectura(self, 'cedula')
        campo_solo_lectura(self, 'genero')

class DocenteForm(forms.Form):
    cargo = forms.ModelChoiceField(label=u"Cargo", required=False, queryset=Cargo.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    nombres = forms.CharField(label='Nombres', required=True, widget=forms.TextInput(attrs={'class': ' form-control','onKeyPress' : 'return solo_letras(event)',  }))
    apellidos = forms.CharField(label='Apellidos', required=True, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    email = forms.CharField(label="Correo electrónico", max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control',}))
    cedula = forms.CharField(label="Cédula", max_length=10, required=False, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_numeros(event)',}))
    genero = forms.ModelChoiceField(label="Género",required=True, queryset=Genero.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control',}))
    telefono_movil = forms.CharField(label="Teléfono móvil", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'(99 123 1234)'}))
    telefono_convencional = forms.CharField(label=u"Teléfono fijo", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control ',}))
    ciudad = forms.CharField(label=u"Ciudad", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Milagro'}))
    direccion = forms.CharField(label=u"Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Av. Quito'}))
    referencia = forms.CharField(label=u"Referencia", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A 2 cuadras..'}))
    foto = ExtFileField(label=u'Seleccione foto', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato png, jpg, jpeg', ext_whitelist=(".png", ".jpg", ".jpeg"), max_upload_size=2621440)


    def editar(self):
        campo_solo_lectura(self, 'cedula')
        campo_solo_lectura(self, 'genero')

class PeriodoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control',  }))
    descripcion = forms.CharField(label='Descripción', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))
    inicio = forms.DateTimeField(label='Fecha inicio',input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}))
    fin = forms.DateTimeField(label='Fecha fin',input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}))
    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))

class TipoRubroForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control',  }))
    descripcion = forms.CharField(label='Descripción', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))

class CursoForm(forms.Form):
    periodo = forms.ModelChoiceField(label=u"Periodo", required=False, queryset=Periodo.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    docente = forms.ModelChoiceField(label=u"Docente a cargo", required=True, queryset=Docente.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control',  }))
    tiporubro = forms.ModelChoiceField(label=u"Tipo rubro", required=True, queryset=TipoOtroRubro.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    costo = forms.CharField(label=u"Costo", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    fechainicio = forms.DateTimeField(label='Fecha inicio', input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}))
    fechafin = forms.DateTimeField(label='Fecha fin', input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control','type': 'date'}))
    fechainicioinscripcion = forms.DateTimeField(label='Fecha inicio inscripción', input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}))
    fechafininscripcion = forms.DateTimeField(label='Fecha fin inscripción', input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control','type': 'date'}))
    inscripcion = forms.BooleanField(label='Inscripción', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))
    tiporubroinscripcion = forms.ModelChoiceField(label=u"Tipo rubro inscripción", required=False, queryset=TipoOtroRubro.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    costoinscripcion = forms.CharField(label=u"Costo inscripción", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    matricula = forms.BooleanField(label='Matrícula', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))
    tiporubromatricula = forms.ModelChoiceField(label=u"Tipo rubro matrícula", required=False, queryset=TipoOtroRubro.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    costomatricula = forms.CharField(label=u"Costo matrícula", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    horasvirtual = forms.CharField(label=u"Número de horas", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    minasistencia = forms.CharField(label=u"Asistencia mínima", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    minnota = forms.CharField(label=u"Nota mínima", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    cupo = forms.CharField(label=u"Cupos", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    gcuotas = forms.BooleanField(label='Genera cuotas', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))
    tiporubrocuota = forms.ModelChoiceField(label=u"Tipo rubro cuota", required=False, queryset=TipoOtroRubro.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    cuotas = forms.CharField(label=u"Número de cuotas", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    oferta = forms.BooleanField(label='Aplica oferta', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))
    costooferta = forms.CharField(label=u"Costo oferta", max_length=50, required=False,widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    observacion = forms.CharField(label='Observacion', required=True, widget=forms.TextInput(attrs={'class': ' form-control', }))
    objetivo = forms.CharField(label='Objetivo', required=True, widget=forms.TextInput(attrs={'class': ' form-control', }))
    contenido = forms.CharField(label='Contenido', required=True, widget=forms.TextInput(attrs={'class': ' form-control', }))
    publicarcurso = forms.BooleanField(label='Publicar curso', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))
    planificacion = ExtFileField(label=u'Planificación', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png, pdf', ext_whitelist=(".jpg", ".png", ".pdf"), max_upload_size=2621440)
    imagen = ExtFileField(label=u'Imagen del curso', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png', ext_whitelist=(".jpg", ".png"), max_upload_size=2621440)
    imagenweb = ExtFileField(label=u'Imagen del curso para web', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png', ext_whitelist=(".jpg", ".png"), max_upload_size=2621440)

    def desactivar_campos(self):
        campo_no_requerido(self, 'planificacion')
        campo_no_requerido(self, 'imagen')
        campo_no_requerido(self, 'imagenweb')
        campo_no_requerido(self, 'periodo')

    def sin_cuotas(self):
        del self.fields['gcuotas']
        del self.fields['cuotas']
        del self.fields['tiporubrocuota']

class VincularModeloEvaluativoForm(forms.Form):
    modelo = forms.ModelChoiceField(label=u"Modelo evaluativo", required=True, queryset=ModeloEvaluativo.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))



class InscribirForm(forms.Form):
    alumno = forms.ModelChoiceField(label=u"Alumno", required=True, queryset=Alumno.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))

class CajaForm(forms.Form):
    encargado = forms.ModelChoiceField(label="Encargado", required=True, queryset=Persona.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control', }))
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control','onKeyPress' : 'return solo_letras(event)',  }))
    descripcion = forms.CharField(label='Descripción', required=True, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))
    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))


class ModeloEvaluativoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control',}))
    notamaxima = forms.DecimalField(initial='0.00', label='Nota máxima', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))
    notaaprobar = forms.DecimalField(initial='0.00', label='Nota para aprobar', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))
    asistenciaaprobar = forms.DecimalField(initial='0.00', label='Asistencia para aprobar', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))
    observaciones = forms.CharField(label='Observaciones', required=False,widget=forms.Textarea(attrs={'class': 'form-control', }))

class DetalleModeloEvaluativoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control',}))
    notaminima = forms.DecimalField(initial='0.00', label='Nota mínima', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))
    notamaxima = forms.DecimalField(initial='0.00', label='Nota máxima', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))
    orden = forms.DecimalField(initial='0', label='Orden', required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'onKeyPress': 'return solo_digitos(event)', }))


class CargoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': ' form-control','onKeyPress' : 'return solo_letras(event)',  }))

class DoctorForm(forms.Form):
    nombre1 = forms.CharField(label='1ª Nombre', required=True,
                             widget=forms.TextInput(attrs={'class': ' form-control', }))
    nombre2 = forms.CharField(label='2ª Nombre', required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control', }))
    apellido1 = forms.CharField(label='1ª Apellido', required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control', }))
    apellido2 = forms.CharField(label='2º Apellido', required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control', }))
    email = forms.CharField(label=u"Correo electrónico", max_length=200, required=True,
                            widget=forms.TextInput(attrs={'class': 'form-control',}))
    cedula = forms.CharField(label=u"Cédula", max_length=10, required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control',}))
    genero = forms.ModelChoiceField(label=u"Gènero",required=True, queryset=Genero.objects.filter(status=True),
                                  widget=forms.Select(attrs={'class': 'form-control',}))

    telefono_movil = forms.CharField(label=u"Teléfono móvil", max_length=50, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'(99 123 1234)'}))
    telefono_convencional = forms.CharField(label=u"Teléfono fijo", max_length=50, required=False,
                                    widget=forms.TextInput(attrs={'class': 'form-control ',}))
    ciudad = forms.CharField(label=u"Ciudad", max_length=50, required=False,
                             widget=forms.TextInput(
                                 attrs={'class': 'form-control', 'placeholder': '(Naranjito)'}))
    direccion = forms.CharField(label=u"Dirección", required=False,
                                widget=forms.TextInput(
                                    attrs={'class': 'form-control', 'placeholder': '(Dirección)'}))
    referencia = forms.CharField(label=u"Referencia",required=False,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control', 'placeholder': '(Referencia)'}))
    especialidad = forms.CharField(label=u"Especialidad", required=False,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control', 'placeholder': '(Especialidad)'}))


    def editar(self):
        campo_solo_lectura(self, 'cedula')
        campo_solo_lectura(self, 'genero')

class AccesoModuloForm(forms.Form):
    grupo = forms.ModelChoiceField(label="Grupo", queryset=Group.objects.all(), widget=forms.Select(attrs={'class': 'form-control', }))
    modulo = forms.ModelChoiceField(label="Módulo", queryset=Modulo.objects.filter(status=True, activo = True), widget=forms.Select(attrs={'class': 'form-control', }))
    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled','checked':'checked'}))

class ConsultaForm(forms.Form):
    diagnostico_previo =  forms.CharField(label='Diagnostio Previo', required=False,
                             widget=forms.Textarea(attrs={'class': 'form-control', }))
    motivoconsulta = forms.CharField(label='Motivo consulta', required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', }))
    descripcionmotivo = forms.CharField(label='Descripción', required=False,
                             widget=forms.Textarea(attrs={'class': 'form-control', }))
    temperatura = forms.CharField(label='Temperatura', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    respiracion = forms.CharField(label='Respiración', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    presionarterial = forms.CharField(label='Presión arterial', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    pulso = forms.CharField(label='Pulso', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    frecuenciacardiaca = forms.CharField(label='Frecuencia cardiaca', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    frecuenciarespiratoria = forms.CharField(label='Frecuencia respiratoria', required=False,
                             widget=forms.NumberInput(attrs={'class': 'form-control', }))
    diagnostico = forms.CharField(label='Diagnóstico', required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control', }))
    observaciondiagnostico = forms.CharField(label='Observación diagnóstico', required=False,
                             widget=forms.Textarea(attrs={'class': 'form-control', }))
    # tratamientos = forms.ModelMultipleChoiceField(Tratamiento.objects.filter(status=True), label=u'Tratamientos', required=False,  widget=forms.SelectMultiple(attrs={'class': 'duallistbox form-control'}))
    observacion =  forms.CharField(label='Observacion', required=False, widget=forms.Textarea(attrs={'class': 'form-control', }))


class TratamientoForm(forms.Form):
    nombre =  forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_letras(event)', }))

    costo = forms.DecimalField(initial='0.00', label='Costo',required=True, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_digitos(event)',}))

    descripcion =  forms.CharField(label='Descripción', required=False,widget=forms.Textarea(attrs={'class': 'form-control', }))



class AbonarCuotaForm(forms.Form):

    abono = forms.DecimalField(initial='0.00', label='Abono',required=True, widget=forms.TextInput(attrs={'class': 'form-control','onKeyPress' : 'return solo_digitos(event)',}))



class HorarioHoraForm(forms.Form):
    hora_inicio = forms.TimeField(label="Hora Inicio", input_formats=['%H:%M'],
                                  widget=DateTimeInput(format='%H:%M',
                                                       attrs={'class': 'form-control'}))
    hora_fin = forms.TimeField(label="Hora Fin", input_formats=['%H:%M'],
                               widget=DateTimeInput(format='%H:%M',
                                                    attrs={'class': 'form-control'}))

    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(
        attrs={'class': 'form-check form-switch ms-2 my-auto is-filled', 'checked': 'checked'}))



class CambiarContraseñaForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le añadimos clases CSS a los inputs
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control '



class FiltroForm(forms.Form):
    fecha_inicio = forms.DateTimeField(input_formats=['%Y-%m-%d'] ,widget= forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control','type':'date'}))
    fecha_fin =forms.DateTimeField(input_formats=['%Y-%m-%d'],widget= forms.DateInput(format='%Y-%m-%d',attrs={'class': 'form-control','type':'date'}))
    docente = ModelChoiceField(label='Docente', queryset=Docente.objects.filter(status=True),  widget=forms.Select(attrs={'class': 'form-control', }))


class PagoForm(forms.Form):
    valor = forms.FloatField(required=True, min_value=0,widget=forms.NumberInput(attrs={'class': ' form-control','step': "0.01"}))
    # iva = forms.IntegerField(widget=forms.NumberInput(attrs={'class': ' form-control','readonly':'readonly'}))
    # subtotal_iva = forms.FloatField(required=True, min_value=0, widget=forms.NumberInput(attrs={'class': ' form-control','step': "0.01",'readonly':'readonly'}))
    valorfinal = forms.FloatField(required=True, min_value=0, widget=forms.NumberInput(attrs={'class': ' form-control','step': "0.01",'readonly':'readonly'}))

class DocumentoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    archivo = ExtFileField(label=u'Seleccione Archivo', help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png, pdf',
                           ext_whitelist=(".jpg", ".png", ".pdf"), max_upload_size=2621440)

class FacturaForm(forms.Form):
    archivo = ExtFileField(label=u'Seleccione Archivo', help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png, pdf',
                           ext_whitelist=(".jpg", ".png", ".pdf"), max_upload_size=2621440)