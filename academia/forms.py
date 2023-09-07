from datetime import datetime
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.forms import DateTimeInput, ModelChoiceField

from administrativo.models import *
from academia.models import TIPO_RECURSOS


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


class AgregarEntregaForm(forms.Form):
    archivo = ExtFileField(label=u'Seleccione Archivo', required=True,
                           help_text=u'Tamaño maximo permitido 2.5Mb, en formato pdf, word',
                           ext_whitelist=(".docx", ".pdf"), max_upload_size=2621440)
    comentario = forms.CharField(label='Comentarios', required=False,widget=forms.Textarea(attrs={'class': 'form-control', }))

    def sin_archivo(self):
        campo_no_requerido(self, 'archivo')

class AgregarActividadForm(forms.Form):
    detalle = forms.ModelChoiceField(label=u"Actividad",required=True, queryset=DetalleModeloEvaluativoA.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control',}))
    nombre = forms.CharField(label='Título', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))
    descripcion = forms.CharField(label='Descripción', required=True, widget=forms.Textarea(attrs={'class': 'form-control', }))
    minnota = forms.CharField(label=u"Nota mínima", max_length=50, required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    maxnota = forms.CharField(label=u"Nota máxima", max_length=50, required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50'}))
    fechamaximasubida = forms.DateField(label=u"Fecha máxima de subida", input_formats=['%Y-%m-%d'], required=False, widget=DateTimeInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}))
    horalimite = forms.TimeField(label=u"Hora máxima", required=True, input_formats=['%H:%M'], widget=DateTimeInput(format='%H:%M', attrs={'class': 'form-control'}))
    imagen = ExtFileField(label=u'Seleccione imagen', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato jpg, png, jpeg', ext_whitelist=(".jpg", ".png", ".jpeg"), max_upload_size=2621440)
    archivo = ExtFileField(label=u'Seleccione archivo', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato pdf, word', ext_whitelist=(".docx", ".pdf"), max_upload_size=2621440)


    def sin_archivo(self):
        campo_no_requerido(self, 'archivo')

    def sin_imagen(self):
        campo_no_requerido(self, 'imagen')

class AgregarTestForm(forms.Form):
    detalle = forms.ModelChoiceField(label=u"Actividad",required=True, queryset=DetalleModeloEvaluativoA.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control',}))
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))
    fecha_inicio = forms.DateTimeField(label='Fecha inicio', required=True, input_formats=['%Y-%m-%d %H:%M:%S'], widget=forms.DateInput(format='%Y-%m-%d %H:%M:%S', attrs={'class': 'form-control', 'type': 'datetime-local'}))
    fecha_nota = forms.DateTimeField(label='Fecha mostrar nota', required=True, input_formats=['%Y-%m-%d %H:%M:%S'], widget=forms.DateInput(format='%Y-%m-%d %H:%M:%S', attrs={'class': 'form-control', 'type': 'datetime-local'}))
    duracion = forms.CharField(label='Duración (hh:mm)', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))
    activo = forms.BooleanField(label='Activo', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check form-switch ms-2 my-auto is-filled'}))

    def clean(self):
        cleaned_data = super().clean()
        duracion = cleaned_data.get('duracion')

        if duracion:
            try:
                horas, minutos = map(int, duracion.split(':'))
                if 0 <= horas <= 23 and 0 <= minutos <= 59:
                    return f'{horas:02d}:{minutos:02d}'
            except ValueError:
                pass

        raise forms.ValidationError('Por favor, ingresa un tiempo válido en el formato "hh:mm".')


class AgregarRecursoForm(forms.Form):
    nombre = forms.CharField(label='Nombre', required=True, widget=forms.TextInput(attrs={'class': 'form-control', }))
    tipo = forms.ChoiceField(choices=TIPO_RECURSOS, label=u'Tipo de recurso', required=True, widget=forms.Select(attrs={'class': 'form-control', }))
    archivo = ExtFileField(label=u'Seleccione archivo', required=False, help_text=u'Tamaño maximo permitido 2.5Mb, en formato pdf, word', ext_whitelist=(".docx", ".pdf"), max_upload_size=2621440)
    enlace = forms.CharField(label='Enlace', required=False, widget=forms.TextInput(attrs={'class': 'form-control', }))


    def sin_archivo(self):
        campo_no_requerido(self, 'archivo')

    def sin_imagen(self):
        campo_no_requerido(self, 'imagen')

class AgregarProfile(forms.Form):
    contacto = forms.ModelChoiceField(label=u"Contacto",required=True, queryset=Persona.objects.filter(status=True), widget=forms.Select(attrs={'class': 'form-control',}))


class FormMensajes(forms.Form):
	mensaje = forms.CharField(widget=forms.Textarea(attrs = {"class": "formulario_ms", "placeholder":"Escribe tu mensaje"}))
