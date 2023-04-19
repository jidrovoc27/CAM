from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Sum

from administrativo.funciones import ModeloBase

class Modulo(ModeloBase):
    nombre = models.CharField(verbose_name="Nombre del módulo", max_length=100, unique=True)
    descripcion = models.CharField(verbose_name="Descripción", default='', max_length=200)
    icono = models.ImageField(verbose_name="Icono", upload_to='icono/')
    ruta = models.CharField(default='', max_length=200, unique=True, verbose_name='Ruta')
    activo = models.BooleanField(verbose_name="¿Módulo activo?")

    class Meta:
        verbose_name = "Módulo del sistema"
        verbose_name_plural = "Módulos del sistema"
        ordering = ['id']
        unique_together = ('ruta',)

    def __str__(self):
        return u'%s' % self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        self.descripcion = self.descripcion.strip().capitalize()
        return super(Modulo, self).save(*args, **kwargs)


class Genero(ModeloBase):
    nombre = models.CharField(max_length=100, verbose_name=u'Género')

    class Meta:
        verbose_name = "Género"
        verbose_name_plural = "Géneros"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.nombre


class Persona(ModeloBase):
    usuario = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=100, verbose_name=u'1er Nombre')
    apellidos = models.CharField(max_length=100, verbose_name=u"1er Apellido")
    email = models.CharField(default='', max_length=200, verbose_name=u"Correo electronico personal")
    cedula = models.CharField( max_length=10, verbose_name=u'Cédula', null=True, blank=True)
    telefono_movil = models.CharField(max_length=10, verbose_name=u"Teléfono móvil", null=True, blank=True)
    telefono_convencional = models.CharField(max_length=10, verbose_name=u"Teléfono convencional", null=True, blank=True)
    genero = models.ForeignKey(Genero, null=True, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=300, verbose_name=u'Direccion', null=True, blank=True)
    referencia = models.CharField(max_length=400, verbose_name=u'Referencia', null=True, blank=True)
    ciudad = models.CharField(max_length=400, verbose_name=u'Referencia', null=True, blank=True)

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['id']

    def __str__(self):
        return u'%s %s' % (self.apellidos, self.nombres)


    def tiene_perfil_persona(self):
        return self.personaperfil_set().exists()

class PersonaPerfil(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    is_profesor = models.BooleanField(default=False, verbose_name=u'Es profesor')
    is_administrador = models.BooleanField(default=False, verbose_name=u'Es administrador')
    is_alumno = models.BooleanField(default=False, verbose_name=u'Es alumno')

    class Meta:
        verbose_name = "Perfil de persona"
        verbose_name_plural = "Perfiles de personas"
        ordering = ['id']

    def __str__(self):
        if self.es_profesor():
            return u'%s' % "PROFESOR"
        elif self.es_administrador():
            return u'%s' % "ADMINISTRADOR"
        elif self.es_alumno():
            return u'%s' % "ALUMNO"
        else:
            return u'%s' % "NO TIENE PERFIL"

    def es_profesor(self):
        return self.es_profesor

    def es_administrador(self):
        return self.es_administrador

    def es_alumno(self):
        return self.es_alumno

class CargoDocente(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Cargo docente"
        verbose_name_plural = u" Cargos docentes"
        ordering = ['nombre']

class Docente(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    contrato = models.CharField(default='', max_length=50, null=True, blank=True, verbose_name=u"Contrato")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.persona


class Alumno(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.persona

    def totalrubros(self):
        total = Rubro.objects.filter(alumno_id=self.id, status=True).aggregate(total=Sum('valor'))
        if not total['total']:
            return 0.00
        return total['total']

    def totalpagos(self):
        lista_rubros = Rubro.objects.filter(alumno_id=self.id, status=True).values_list('id')
        total = Pago.objects.filter(rubro_id__in=lista_rubros, status=True).aggregate(total=Sum('valorfinal'))
        valorpago = 0.00
        if total['total']:
            valorpago = total['total']
        return ("{0:.0f}".format(valorpago))

    def verificar_estadocuenta(self):
        lista_rubros = Rubro.objects.filter(alumno_id=self.id, cancelado=False, status=True)
        tienevalorapagar = False
        if lista_rubros:
            tienevalorapagar = True
        return tienevalorapagar

class AccesoModulo(ModeloBase):
    grupo = models.ForeignKey(Group,  on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Acceso a módulo"
        verbose_name_plural = "Acceso a módulos"
        ordering = ['id']

    def __str__(self):
        return u'%s - %s - %s' % (self.grupo,self.modulo, self.activo)


class TiempoAntesRecordatorioCorreo(ModeloBase):
    dias_antes = models.CharField(max_length=100, verbose_name=u'Días antes del recordatorio')
    horas_antes = models.CharField(max_length=100, verbose_name=u'Horas antes del recordatorio')
    minutos_antes = models.CharField(max_length=100, verbose_name=u'Minutos antes del recordatorio')

    def __str__(self):
        return u'Días: %s | Horas: %s | Minutos: %s' % (self.dias_antes,self.horas_antes,self.minutos_antes)

class Rubro(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=300, null=True)
    valor = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Valor')
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)
    cancelado = models.BooleanField(default=False)

    def __str__(self):
        return u'%s - Consulta: %s' % (self.nombre, self.valor)

    def totalpagos(self):
        total = Pago.objects.filter(rubro_id=self.id, status=True).aggregate(total=Sum('valorfinal'))
        totalpagado = 0.00
        if total['total']:
            totalpagado = total['total']
        return ("{0:.0f}".format(totalpagado))

    def saldorestante(self):
        totalpagos = Pago.objects.filter(rubro_id=self.id, status=True).aggregate(total=Sum('valorfinal'))
        saldofinal = self.valor
        if totalpagos['total']:
            saldofinal = float(self.valor) - float(totalpagos['total'])
        return ("{0:.0f}".format(saldofinal))

    def numero_pagos_realizados(self):
        cantidad_pagos = Pago.objects.filter(rubro_id=self.id, status=True).count()
        return cantidad_pagos


class Pago(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    rubro = models.ForeignKey(Rubro, on_delete=models.CASCADE)
    valor = models.FloatField(default=0, verbose_name=u'Pago')
    # iva = models.DecimalField(max_digits=30, decimal_places=2, default=12, verbose_name=u'Iva')
    # subtotal_iva = models.FloatField(default=0, verbose_name=u'Subtotal iva')
    valorfinal = models.FloatField(default=0, verbose_name=u'Valor final')
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)

class Factura(ModeloBase):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)
    archivo = models.FileField(upload_to='facturas', blank=True, null=True, verbose_name=u'Facturas')

class Documentos(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, blank=True, null=True)
    nombre = models.CharField(max_length=500, null=True)
    archivo = models.FileField(upload_to='documentos', blank=True, null=True, verbose_name=u'Documentos')
