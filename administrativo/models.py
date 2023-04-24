from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Sum
import datetime
from datetime import datetime

from administrativo.funciones import *

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

class Periodo(ModeloBase):
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción')
    inicio = models.DateField(verbose_name=u'Fecha inicio')
    fin = models.DateField(verbose_name=u'Fecha fin')
    activo = models.BooleanField(default=True, verbose_name=u'Visible')

    def __str__(self):
        return u'%s: %s a %s' % (self.nombre, self.inicio.strftime('%d-%m-%Y'), self.fin.strftime('%d-%m-%Y'))

    class Meta:
        verbose_name = u"Periodo de cursos"
        verbose_name_plural = u"Periodos de cursos"
        ordering = ['-id']

    def total_cursos(self):
        return Curso.objects.filter(status=True, periodo=self).count()

ESTADO_CURSO = (
    (1, u'CREADO'),
    (2, u'APERTURADO'),
    (3, u'CERRADO'),
    (4, u'CANCELADO'),
)

TIPO_RUBRO = (
    (1, u'SERVICIO'),
    (2, u'BIEN'),
    (3, u'RENTA INVERSIONES'),
)

MODALIDAD_CAPACITACION = (
    (1, u'VIRTUAL'),
    (2, u'PRESENCIAL'),
)

class TipoOtroRubro(ModeloBase):
    nombre = models.CharField(default='', max_length=300, verbose_name=u'Nombre')
    descripcion = models.CharField(default='', max_length=800, verbose_name=u'Descripción')
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')
    tiporubro = models.IntegerField(choices=TIPO_RUBRO, default=1, verbose_name=u"Tipo de Rubro")

    def __str__(self):
        return u'%s' % (self.nombre)

    class Meta:
        verbose_name = u"Tipo otro rubro"
        verbose_name_plural = u"Tipo otros rubros"
        ordering = ['-id']

class ModeloEvaluativo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")
    fecha = models.DateField(verbose_name=u"Fecha")
    principal = models.BooleanField(default=False, verbose_name=u"Principal")
    notamaxima = models.FloatField(default=0, verbose_name=u'Nota maxima')
    notaaprobar = models.FloatField(default=0, verbose_name=u'Nota para aprobar')
    asistenciaaprobar = models.FloatField(default=0, verbose_name=u'Asistencia para aprobar')
    observaciones = models.TextField(default='', max_length=200, verbose_name=u'Observaciones')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Modelo evaluativo"
        verbose_name_plural = u"Modelos evaluativos"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(ModeloEvaluativo, self).save(*args, **kwargs)


class DetalleModeloEvaluativo(ModeloBase):
    modelo = models.ForeignKey(ModeloEvaluativo, on_delete=models.PROTECT, verbose_name=u"Modelo")
    nombre = models.CharField(default='', max_length=10, verbose_name=u"Nombre campo")
    notaminima = models.FloatField(default=0, verbose_name=u'Nota minima')
    notamaxima = models.FloatField(default=0, verbose_name=u'Nota maxima')
    orden = models.IntegerField(default=0, verbose_name=u"Orden en acta")

    def __str__(self):
        return u'%s (%s a %s)' % (self.nombre, self.notaminima.__str__(), self.notamaxima.__str__())

    class Meta:
        verbose_name = u"Detalle del modelo evaluativo"
        verbose_name_plural = u"Detalles de los modelos evaluativos"
        ordering = ['orden']



class Documentos(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, blank=True, null=True)
    archivo = models.FileField(upload_to='documentos', blank=True, null=True, verbose_name=u'Documentos')
    nombre = models.CharField(max_length=500, null=True)

class Curso(ModeloBase):
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT, verbose_name=u'Periodo', blank=True, null=True)
    modeloevaluativo = models.ForeignKey(ModeloEvaluativo, on_delete=models.PROTECT, verbose_name=u'Modelo Evaluativo', blank=True, null=True)
    nombre = models.CharField(max_length=500, verbose_name=u'Nombre')
    estado = models.IntegerField(choices=ESTADO_CURSO, blank=True, null=True, verbose_name=u'Estado Curso')
    tiporubro = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para cuota", on_delete=models.PROTECT, blank=True, null=True)
    tiporubroinscripcion = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para inscripcion", on_delete=models.PROTECT, blank=True, null=True)
    tiporubromatricula = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para matricula", on_delete=models.PROTECT, blank=True, null=True)
    tiporubrocuota = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para cuotas", on_delete=models.PROTECT, blank=True, null=True)
    horasvirtual = models.IntegerField(default=0, verbose_name=u'Horas Virtuales')
    minasistencia = models.IntegerField(default=0, verbose_name=u'Asistencia mínima para aprobar')
    minnota = models.IntegerField(default=0, verbose_name=u'Nota mínima para aprobar')
    cupo = models.IntegerField(default=0, verbose_name=u'Cupo')
    cuotas = models.IntegerField(default=0, verbose_name=u'Cuotas')
    costo = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u"Costo del curso")
    gcuotas = models.BooleanField(default=False, verbose_name=u"El curso genera cuotas?")
    inscripcion = models.BooleanField(default=False, verbose_name=u"El curso aplica inscripción?")
    costoinscripcion = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u"Costo de la inscripción")
    oferta = models.BooleanField(default=False, verbose_name=u"Aplica oferta?")
    costooferta = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u"Costo del curso aplicando oferta")
    matricula = models.BooleanField(default=False, verbose_name=u"Matrícula")
    costomatricula = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u"Costo de la matrícula")
    modalidad = models.IntegerField(choices=MODALIDAD_CAPACITACION, blank=True, null=True, verbose_name=u'Modalidad DEL CURSO')
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT, verbose_name=u"Docente")
    fechainicio = models.DateField(blank=True, null=True)
    fechafin = models.DateField(blank=True, null=True)
    fechainicioinscripcion = models.DateField(blank=True, null=True)
    fechafininscripcion = models.DateField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True, verbose_name=u"Observacion")
    objetivo = models.TextField(blank=True, null=True, verbose_name=u"Objetivo")
    contenido = models.TextField(blank=True, null=True, verbose_name=u"Contenido")
    visualizar = models.BooleanField(default=False, verbose_name=u"Visualizar")
    publicarcurso = models.BooleanField(default=False, verbose_name=u"Publicar")
    planificacion = models.FileField(upload_to='planificacioncurso', verbose_name='Planificación', null=True, blank=True)
    fondoweb = models.ImageField(verbose_name="Fondo para página web", upload_to='fondoweb', null=True, blank=True)
    fondocursos = models.ImageField(verbose_name="Fondo para cursos", upload_to='fondocursos', null=True, blank=True)
    # fondocertificado = models.ImageField(upload_to='fondocertificados', verbose_name='Fondo', null=True, blank=True)
    finalizarcurso = models.BooleanField(default=False, verbose_name='¿Curso terminado?', null=True, blank=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.nombre)

ESTADO_INSCRITO = (
    (1, u'APROBADO'),
    (2, u'REPROBADO'),
)

class InscritoCurso(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT, verbose_name=u"Alumno")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, verbose_name=u"Curso")
    estado = models.IntegerField(default=2, choices=ESTADO_INSCRITO, blank=True, null=True, verbose_name=u'Modalidad DEL CURSO')

    class Meta:
        verbose_name = "Inscrito Curso"
        verbose_name_plural = "Inscritos por curso"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.alumno)

    def generar_rubros(self, curso):
        try:
            if curso.inscripcion:
                rubroinscripcion = Rubro(nombre=curso.tiporubroinscripcion.nombre + ' - ' + self.nombre,
                              tiporubro=curso.tiporubroinscripcion, curso=curso, alumno=self, tipocuota=1, valor=curso.costoinscripcion,
                              fecha=datetime.now().date(), cancelado=False)
                rubroinscripcion.save()

            if curso.matricula:
                rubromatricula = Rubro(nombre=curso.tiporubromatricula.nombre + ' - ' + self.nombre,
                              tiporubro=curso.tiporubromatricula, curso=curso, alumno=self, tipocuota=2, valor=curso.costomatricula,
                              fecha=datetime.now().date(), cancelado=False)
                rubromatricula.save()

            if curso.gcuotas:
                cuotas = CuotasCurso.objects.filter(status=True, curso=curso)
                for cuota in cuotas:
                    rubrocuotas = Rubro(nombre=curso.tiporubrocuota.nombre + ' - ' + self.nombre,
                                  tiporubro=curso.tiporubrocuota, curso=curso, alumno=self, cuota=cuota.numerocuota, tipocuota=3, valor=cuota.valor,
                                  fecha=datetime.now().date(), cancelado=False)
                    rubrocuotas.save()

            if not curso.inscripcion and not curso.matricula and not curso.gcuotas:
                nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + self.nombre,
                                       tiporubro=curso.tiporubro, curso=curso, alumno=self, tipocuota=4,
                                       valor=curso.costo,
                                       fecha=datetime.now().date(), cancelado=False)
                nuevorubrocurso.save()

            if curso.inscripcion and not curso.matricula and not curso.gcuotas:
                diferenciavalor = solo_2_decimales(curso.costo - curso.costoinscripcion, 2)
                if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + self.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, alumno=self, tipocuota=4,
                                            valor=curso.costo,
                                            fecha=datetime.now().date(), cancelado=False)
                    nuevorubrocurso.save()

            if not curso.inscripcion and curso.matricula and not curso.gcuotas:
                diferenciavalor = solo_2_decimales(curso.costo - curso.costomatricula, 2)
                if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + self.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, alumno=self, tipocuota=4,
                                            valor=curso.costo,
                                            fecha=datetime.now().date(), cancelado=False)
                    nuevorubrocurso.save()
            return True
        except Exception as ex:
            return False

class NotaInscrito(ModeloBase):
    inscrito = models.ForeignKey(InscritoCurso, on_delete=models.PROTECT, verbose_name=u"Alumno")
    modelo = models.ForeignKey(DetalleModeloEvaluativo, on_delete=models.PROTECT, verbose_name=u"Modelo Evaluativo: N1, N2, N3, etc.")
    notafinal = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Nota final')

    class Meta:
        verbose_name = "Nota del inscrito"
        verbose_name_plural = "Notas del inscrito"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.notafinal)


TIPO_CUOTA = (
    (1, u'INSCRIPCION'),
    (2, u'MATRICULA'),
    (3, u'CUOTA'),
    (4, u'CANTIDAD'),
)


class Rubro(ModeloBase):
    tiporubro = models.ForeignKey(TipoOtroRubro, on_delete=models.CASCADE, blank=True, null=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, blank=True, null=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=300, blank=True, null=True)
    cuota = models.IntegerField(default=0, verbose_name=u'Cuota')
    tipocuota = models.IntegerField(choices=TIPO_CUOTA, default=3)
    subtotal = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Subtotal')
    valor = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Valor')
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)
    fechavencimiento = models.DateField(verbose_name=u'Fecha vencimiento', auto_now_add=True, null=True)
    cancelado = models.BooleanField(default=False, blank=True, null=True)

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


class CuotasCurso(ModeloBase):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, verbose_name=u'Curso', blank=True, null=True)
    numerocuota = models.IntegerField(default=0, verbose_name=u'Número de la cuota', blank=True, null=True)
    inicio = models.DateField(verbose_name=u'Fecha inicio', blank=True, null=True)
    fin = models.DateField(verbose_name=u'Fecha fin', blank=True, null=True)
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor de la cuota')


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

