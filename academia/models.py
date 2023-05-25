from django.db import models

# Create your models here.
from administrativo.models import *
from administrativo.funciones import *
from django.db.models import Q, F, Count
from django.apps import apps

class PeriodoA(ModeloBase):
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre', blank=True, null=True)
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción', blank=True, null=True)
    inicio = models.DateField(verbose_name=u'Fecha inicio', blank=True, null=True)
    fin = models.DateField(verbose_name=u'Fecha fin', blank=True, null=True)
    activo = models.BooleanField(default=True, verbose_name=u'Visible', blank=True, null=True)

    def __str__(self):
        return u'%s: %s a %s' % (self.nombre, self.inicio.strftime('%d-%m-%Y'), self.fin.strftime('%d-%m-%Y'))

    class Meta:
        verbose_name = u"Periodo de cursos"
        verbose_name_plural = u"Periodos de cursos"
        ordering = ['-id']

    def total_cursos(self):
        return CursoA.objects.filter(status=True, periodo=self).count()

class ModeloEvaluativoA(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre", blank=True, null=True)
    fecha = models.DateField(verbose_name=u"Fecha", blank=True, null=True)
    principal = models.BooleanField(default=False, verbose_name=u"Principal", blank=True, null=True)
    notamaxima = models.FloatField(default=0, verbose_name=u'Nota maxima', blank=True, null=True)
    notaaprobar = models.FloatField(default=0, verbose_name=u'Nota para aprobar', blank=True, null=True)
    asistenciaaprobar = models.FloatField(default=0, verbose_name=u'Asistencia para aprobar', blank=True, null=True)
    observaciones = models.TextField(default='', max_length=200, verbose_name=u'Observaciones', blank=True, null=True)
    activo = models.BooleanField(default=True, verbose_name=u"Activo", blank=True, null=True)

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Modelo evaluativo"
        verbose_name_plural = u"Modelos evaluativos"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(ModeloEvaluativoA, self).save(*args, **kwargs)

    def detallecalificacion(self):
        return DetalleModeloEvaluativoA.objects.filter(status=True, modelo=self)

class DetalleModeloEvaluativoA(ModeloBase):
    modelo = models.ForeignKey(ModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u"Modelo", blank=True, null=True)
    nombre = models.CharField(default='', max_length=10, verbose_name=u"Nombre campo", blank=True, null=True)
    notaminima = models.FloatField(default=0, verbose_name=u'Nota minima', blank=True, null=True)
    notamaxima = models.FloatField(default=0, verbose_name=u'Nota maxima', blank=True, null=True)
    orden = models.IntegerField(default=0, verbose_name=u"Orden en acta", blank=True, null=True)

    def __str__(self):
        return u'%s (%s a %s)' % (self.nombre, self.notaminima.__str__(), self.notamaxima.__str__())

    class Meta:
        verbose_name = u"Detalle del modelo evaluativo"
        verbose_name_plural = u"Detalles de los modelos evaluativos"
        ordering = ['orden']

    def detalleactividades(self):
        return DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=self)

    def total_actividad(self, inscrito_id):
        try:
            detalleactividad = lista_actividades = conteo = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=self)
            lista_actividades = lista_actividades.values_list('id')
            conteo = conteo.count()
            totalnotas = NotaInscritoActividadA.objects.filter(status=True, actividad_id__in=detalleactividad, inscrito_id=inscrito_id).aggregate(total=Sum('nota'))

            totalnotas = totalnotas['total'] if totalnotas['total'] else 0
            if conteo > 0 and totalnotas:
                resultado = totalnotas / conteo
            else:
                resultado = 0
            return resultado
        except Exception as ex:
            pass

class DocenteA(ModeloBase):
    persona = models.ForeignKey('administrativo.Persona', on_delete=models.CASCADE, null=True, blank=True)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    contrato = models.CharField(default='', max_length=50, null=True, blank=True, verbose_name=u"Contrato")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.persona

ESTADO_CURSO = (
    (1, u'CREADO'),
    (2, u'APERTURADO'),
    (3, u'CERRADO'),
    (4, u'CANCELADO'),
)

MODALIDAD_CAPACITACION = (
    (1, u'VIRTUAL'),
    (2, u'PRESENCIAL'),
)

class CursoA(ModeloBase):
    periodo = models.ForeignKey(PeriodoA, on_delete=models.PROTECT, verbose_name=u'Periodo', blank=True, null=True)
    modeloevaluativo = models.ForeignKey(ModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u'Modelo Evaluativo', blank=True, null=True)
    idcursoadministrativo = models.ForeignKey('administrativo.Curso', on_delete=models.PROTECT, verbose_name=u'Curso administrativo', blank=True, null=True)
    nombre = models.CharField(max_length=500, verbose_name=u'Nombre', blank=True, null=True)
    estado = models.IntegerField(choices=ESTADO_CURSO, blank=True, null=True, verbose_name=u'Estado Curso')
    horasvirtual = models.IntegerField(default=0, verbose_name=u'Horas Virtuales', blank=True, null=True)
    minasistencia = models.IntegerField(default=0, verbose_name=u'Asistencia mínima para aprobar', blank=True, null=True)
    minnota = models.IntegerField(default=0, verbose_name=u'Nota mínima para aprobar', blank=True, null=True)
    modalidad = models.IntegerField(default=1, choices=MODALIDAD_CAPACITACION, blank=True, null=True, verbose_name=u'Modalidad DEL CURSO')
    docente = models.ForeignKey(DocenteA, on_delete=models.PROTECT, verbose_name=u"Docente", blank=True, null=True)
    fechainicio = models.DateField(blank=True, null=True)
    fechafin = models.DateField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True, verbose_name=u"Observacion", max_length=1000)
    objetivo = models.TextField(blank=True, null=True, verbose_name=u"Objetivo", max_length=1000)
    contenido = models.TextField(blank=True, null=True, verbose_name=u"Contenido", max_length=1000)
    visualizar = models.BooleanField(default=False, verbose_name=u"Visualizar")
    planificacion = models.FileField(upload_to='planificacioncurso', verbose_name='Planificación', null=True, blank=True)
    fondoweb = models.ImageField(verbose_name="Fondo para página web", upload_to='fondoweb', null=True, blank=True)
    fondocursos = models.ImageField(verbose_name="Fondo para cursos", upload_to='fondocursos', null=True, blank=True)
    finalizarcurso = models.BooleanField(default=False, verbose_name='¿Curso terminado?', null=True, blank=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.nombre)

    def detallecalificacion(self):
        return DetalleModeloEvaluativoA.objects.filter(status=True, modelo=self.modeloevaluativo)

    def misrecursos(self):
        return RecursosCurso.objects.filter(status=True, curso=self)

ESTADO_ACTIVIDAD = (
    (1, u'ACTIVO'),
    (2, u'INACTIVO'),
)

TIPO_RECURSOS = (
    (1, u'RECURSO'),
    (2, u'ENLACE'),
)

class RecursosCurso(ModeloBase):
    curso = models.ForeignKey(CursoA, on_delete=models.PROTECT, verbose_name=u'Curso', blank=True, null=True)
    nombre = models.CharField(max_length=500, verbose_name=u'Nombre del recurso', blank=True, null=True)
    tipo = models.IntegerField(default=1, choices=TIPO_RECURSOS, blank=True, null=True, verbose_name=u'Tipo de recurso')
    archivo = models.FileField(upload_to='recursos', verbose_name='Archivo recurso', null=True, blank=True)
    enlace = models.CharField(max_length=500, verbose_name=u'Enlace', blank=True, null=True)

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.nombre)

class DetalleActividadesModeloEvaluativoA(ModeloBase):
    detalle = models.ForeignKey(DetalleModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u'N1, N2, N3, etc.', blank=True, null=True)
    nombre = models.CharField(max_length=500, verbose_name=u'Nombre', blank=True, null=True)
    descripcion = models.CharField(max_length=5000, verbose_name=u'Descripción de la actividad a realizar', blank=True, null=True)
    imagen = models.FileField(upload_to='imagenactividad', blank=True, null=True, verbose_name=u'Imagen del deber')
    archivo = models.FileField(upload_to='archivoactividad', blank=True, null=True, verbose_name=u'Archivo como ayuda del deber')
    minnota = models.IntegerField(default=7, verbose_name=u'Nota mínima para aprobar el deber', blank=True, null=True)
    maxnota = models.IntegerField(default=10, verbose_name=u'Nota máxima para aprobar el deber', blank=True, null=True)
    fechaminimasubida = models.DateField(verbose_name=u"Fecha mínima que el inscrito puede comenzar subir el deber", blank=True, null=True)
    fechamaximasubida = models.DateField(verbose_name=u"Fecha máxima que el inscrito puede subir el deber", blank=True, null=True)
    horalimite = models.TimeField(verbose_name=u'Hora limite', blank=True, null=True)
    estado = models.IntegerField(choices=ESTADO_ACTIVIDAD, blank=True, null=True, verbose_name=u'Estado de la actividad')

    def __str__(self):
        return u'%s' % (self.nombre)

    class Meta:
        verbose_name = u"Tarea que el docente crea"
        verbose_name_plural = u"Tareas que el docente crea"
        ordering = ['-id']

    def nota_calificada(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, actividad=self, inscrito_id=inscrito)
        if verifica:
            return verifica.first().nota
        return '--'

    def registra_actividad(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, actividad=self, inscrito_id=inscrito)
        if verifica:
            return True
        return False

    def actividad_entregada(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, actividad=self, inscrito_id=inscrito)
        if verifica:
            return verifica.first()
        return False

    def tiene_tarea(self, inscrito):
        nota = NotaInscritoActividadA.objects.filter(status=True, actividad=self, inscrito_id=inscrito)
        if nota:
            return nota.first().tarea
        return False



class InscritoCursoA(ModeloBase):
    curso = models.ForeignKey(CursoA, on_delete=models.PROTECT, verbose_name=u'Curso de la academia', blank=True, null=True)
    inscrito = models.ForeignKey('administrativo.Persona', on_delete=models.PROTECT, verbose_name=u'Inscrito', blank=True, null=True)
    certificadopdf = models.FileField(upload_to='certificadoscursos', blank=True, null=True, verbose_name=u'Certificado PDF')

    def __str__(self):
        return u'%s' % (self.inscrito)

    class Meta:
        verbose_name = u"Inscrito"
        verbose_name_plural = u"Inscritos"
        ordering = ['-id']

    def calcularpromedio(self, curso_id):
        cursoacad = CursoA.objects.get(id=int(curso_id))
        modeloadm = cursoacad.modeloevaluativo
        detalles = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=modeloadm)
        conteo = detalles.count()
        sumnotas = 0
        for detalle in detalles:
            actividad = conteosum = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=detalle)
            actividad = actividad.values_list('id', flat=True)
            conteosum = conteosum.count()
            totalnota = NotaInscritoActividadA.objects.filter(status=True, actividad_id__in=actividad, inscrito=self).aggregate(total=Sum('nota'))
            if totalnota['total']:
                conteosum = solo_2_decimales(totalnota['total'] / conteosum, 2)
                sumnotas += conteosum

        if conteo > 0 and sumnotas:
            resultado = sumnotas / conteo
        else:
            resultado = 0
        return resultado

ESTADO_TAREA = (
    (1, 'NO CALIFICADO'),
    (2, 'CALIFICADO'),
)

class NotaInscritoActividadA(ModeloBase):
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.PROTECT, verbose_name=u'Inscrito que sube la tarea', blank=True, null=True)
    actividad = models.ForeignKey(DetalleActividadesModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u'La actividad que sube la tarea', blank=True, null=True)
    tarea = models.FileField(upload_to='tareainscrito', blank=True, null=True, verbose_name=u'Tarea que sube el inscrito')
    nota = models.FloatField(default=0, verbose_name=u'Nota de la tarea', blank=True, null=True)
    fechasubida = models.DateField(verbose_name=u"Fecha que sube el inscrito", blank=True, null=True)
    estado = models.IntegerField(choices=ESTADO_TAREA, default=1, verbose_name=u'Estado de la actividad')
    entregado = models.BooleanField(default=False, verbose_name=u'El deber fue entregado o no')
    calificado = models.BooleanField(default=False, verbose_name=u'El deber fue calificado o no')
    comentario = models.CharField(verbose_name="Comentario de la tarea", default='', max_length=200)

    def __str__(self):
        return u'%s' % (self.nota)

    class Meta:
        verbose_name = u"Tarea que el inscrito sube"
        verbose_name_plural = u"Tareas que el inscrito sube"
        ordering = ['-id']

