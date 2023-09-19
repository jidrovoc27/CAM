from django.db import models
import random

# Create your models here.
from administrativo.models import *
from administrativo.funciones import *
from django.db.models import Q, F, Count
from django.apps import apps
from django.utils import timezone
from datetime import timedelta

tipo_test = (
    (1, u'Normal'),
    (2, u'Recuperación'),
)

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

    def detalleexamenes(self):
        return Examen.objects.filter(status=True, detalle=self, activo=True, aplicarecuperacion=False)

    def total_actividad(self, inscrito_id):
        try:
            #TOTAL DE ACTIVIDADES CON RESPECTO A LAS TAREAS
            detalleactividad = lista_actividades = count_actividades = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=self)
            lista_actividades = lista_actividades.values_list('id')
            count_actividades = count_actividades.count()

            #TOTAL DE EXÁMENES
            examenes = lista_examenes = count_exam = Examen.objects.filter(status=True, detalle=self, activo=True, aplicarecuperacion=False)
            lista_examenes = lista_examenes.values_list('id')
            count_examenes = count_exam.count()

            totalnotas_actividades = NotaInscritoActividadA.objects.filter(status=True, actividad_id__in=detalleactividad, inscrito_id=inscrito_id).aggregate(total=Sum('nota'))
            totalnotas_examenes = NotaInscritoActividadA.objects.filter(status=True, examen_id__in=lista_examenes, inscrito_id=inscrito_id).aggregate(total=Sum('nota'))

            total_conteo = count_actividades + count_examenes

            totalnotas_actividades = totalnotas_actividades['total'] if totalnotas_actividades['total'] else 0
            totalnotas_examenes = totalnotas_examenes['total'] if totalnotas_examenes['total'] else 0
            totalnotas = totalnotas_actividades + totalnotas_examenes
            if total_conteo > 0 and totalnotas:
                resultado = totalnotas / total_conteo
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

    def traer_inscrito(self, alumno):
        inscrito = InscritoCursoA.objects.filter(status=True, curso=self, inscrito_id=alumno)
        if inscrito:
            return inscrito.first()
        return None

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
            #CALCULAR LAS TAREAS
            actividad = conteoactv = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=detalle)
            actividad = actividad.values_list('id', flat=True)
            conteoactv = conteoactv.count()

            #CALCULAR EXÁMENES
            examenes = conteoexam = Examen.objects.filter(status=True, detalle=detalle, activo=True, aplicarecuperacion=False)
            examenes = examenes.values_list('id', flat=True)
            conteoexam = conteoexam.count()
            conteosum = conteoactv + conteoexam

            #CONSULTA LAS NOTAS DE TODAS LAS TAREAS Y ÉXAMENES YA SEAN ENTREGADAS O NO
            totalnota = NotaInscritoActividadA.objects.filter(Q(status=True), (Q(actividad_id__in=actividad) | Q(examen_id__in=examenes)), inscrito=self).aggregate(total=Sum('nota'))

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

class Examen(ModeloBase):
    detalle = models.ForeignKey(DetalleModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u'N1, N2, N3, etc.', blank=True, null=True)
    tipo = models.IntegerField(default=1, choices=tipo_test, blank=True, null=True, verbose_name=u'Normal o recuperación?')
    nombre = models.CharField(max_length=255, blank=True, null=True)
    fecha_inicio = models.DateTimeField(default=timezone.now, blank=True, null=True)
    fecha_nota = models.DateTimeField(default=timezone.now, blank=True, null=True)
    activo = models.BooleanField(default=True, verbose_name=u'Activo')
    aplicarecuperacion = models.BooleanField(default=False, verbose_name=u'Está habilitado para recuperación?')
    duracion = models.DurationField(blank=True, null=True)
    numeropregunta = models.IntegerField(default=0, verbose_name=u"Es la cantidad de preguntas que se tomarán en cuenta para que sean aleatorias", blank=True, null=True)
    tiempo_restante = models.DurationField(blank=True, null=True)

    # def save(self, *args, **kwargs):
    #     tiempo_transcurrido = timezone.now() - self.hora_inicio
    #     self.tiempo_restante = self.tiempo_restante - tiempo_transcurrido
    #     super().save(*args, **kwargs)

    def __str__(self):
        return u'%s - Inicio: %s - Duración: %s' % (self.nombre, self.fecha_inicio, self.duracion)

    def fecha_limite_examen(self):
        return self.fecha_inicio + timedelta(seconds=self.duracion.seconds)

    def examen_entregada(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, examen=self, inscrito_id=inscrito)
        if verifica.exists():
            return True
        return False
    def rindio_examen(self, inscrito):
        nota = NotaInscritoActividadA.objects.filter(status=True, examen=self, inscrito_id=inscrito)
        if nota.exists():
            return True
        return False

    def generar_preguntas_aleatorias(self, idinscrito, request):
        preguntas_asignadas_alumno = None
        consultar_preguntas_asignadas = PreguntaAsignada.objects.filter(status=True, examen=self, inscrito_id=idinscrito)
        if not consultar_preguntas_asignadas.exists():
            preguntas_seleccionadas = random.sample(list(self.pregunta_set.filter(status=True)), self.numeropregunta)
            ids_preguntas = [preguntaselecc.id for preguntaselecc in preguntas_seleccionadas]
            for idpregunta in ids_preguntas:
                preasig = PreguntaAsignada(examen=self, pregunta_id=idpregunta, inscrito_id=idinscrito)
                preasig.save(request)
            preguntasasignadas = PreguntaAsignada.objects.filter(status=True, examen=self, inscrito_id=idinscrito)
            preguntas_asignadas_alumno = Pregunta.objects.filter(status=True, id__in=preguntasasignadas.values_list('pregunta_id', flat=True))
        else:
            preguntas_asignadas_alumno = Pregunta.objects.filter(status=True, id__in=consultar_preguntas_asignadas.values_list('pregunta_id', flat=True))
        return preguntas_asignadas_alumno.order_by('id')

    def consultar_preguntas_asignadas(self, idinscrito):
        preguntas_asignadas_alumno = None
        consultar_preguntas_asignadas = PreguntaAsignada.objects.filter(status=True, examen=self, inscrito_id=idinscrito)
        if consultar_preguntas_asignadas.exists():
            preguntas_asignadas_alumno = Pregunta.objects.filter(status=True, id__in=consultar_preguntas_asignadas.values_list('pregunta_id', flat=True))
        return preguntas_asignadas_alumno.order_by('id')

    #FUNCIÓN QUE PERMITA CALCULAR LA NOTA FINAL DEL CUESTIONARIO EN CASO DE QUE SE CIERRE POR MOTIVO DE FECHA DE CIERRE DEL CUESTIONARIO.
    def calcular_notafinal(self, inscrito, fechaactual, request):
        if fechaactual > self.fecha_limite_examen() and self.pregunta_set.filter(status=True):
            if not self.rindio_examen(inscrito):
                notafinal = 0
                examenalumno = ExamenAlumno.objects.filter(status=True, examen=self, inscrito_id=inscrito)
                if examenalumno.exists():
                    examenalumno = examenalumno.first()
                    preguntas = Pregunta.objects.filter(status=True, examen=self)
                    for pregunta in preguntas:
                        calificacion = pregunta.calificacion
                        literalcorrecto = Literal.objects.filter(status=True, pregunta=pregunta, es_correcta=True)
                        if literalcorrecto.exists():
                            literalcorrecto = literalcorrecto.first()
                            pregunta_fue_contestada = RespuestaAlumno.objects.filter(status=True,
                                                                                     examenalumno=examenalumno,
                                                                                     pregunta=pregunta)
                            if pregunta_fue_contestada.exists():
                                respuesta_alumno = pregunta_fue_contestada.first()
                                calificacion = calificacion if respuesta_alumno.respuesta_escogida == literalcorrecto else 0
                                respuesta_alumno.es_correcta = True if respuesta_alumno.respuesta_escogida == literalcorrecto else False
                                respuesta_alumno.calificacion = calificacion
                                respuesta_alumno.save(request)
                                notafinal += calificacion
                    examenalumno.estado = 2
                    examenalumno.fecha_termina = fechaactual
                    examenalumno.calificacionfinal = notafinal
                    examenalumno.save(request)
                    # CREA LA NOTA PARA PROMEDIAR
                    notaexamen = NotaInscritoActividadA.objects.filter(status=True, inscrito_id=inscrito,
                                                                       examen=self)
                    if not notaexamen.exists():
                        notaexamen = NotaInscritoActividadA(inscrito_id=inscrito, examen=self, nota=notafinal)
                        notaexamen.save(request)

    def registra_examen(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, examen=self, inscrito_id=inscrito)
        if verifica:
            return True
        return False

    def examalum(self, inscrito):
        examalumno = self.examenalumno_set.filter(status=True, inscrito_id=inscrito)
        if examalumno.exists():
            return examalumno.first()

    def tiempo_restante_en_segundos(self):
        tiempo_transcurrido = timezone.now() - self.hora_inicio
        tiempo_restante = self.tiempo_restante - tiempo_transcurrido
        return max(tiempo_restante.total_seconds(), 0)

    def nota_calificada(self, inscrito):
        verifica = NotaInscritoActividadA.objects.filter(status=True, examen=self, inscrito_id=inscrito)
        if verifica:
            return verifica.first().nota
        return '--'

    def cantidad_preguntas(self):
        return Pregunta.objects.filter(status=True, examen=self).count()

class Pregunta(ModeloBase):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, blank=True, null=True)
    enunciado = models.TextField(blank=True, null=True)
    calificacion = models.FloatField(default=0, verbose_name=u'Especifica cuántos puntos vale la pregunta', blank=True, null=True)

    def __str__(self):
        return u'%s - Enunciado: %s - Calificación: %s' % (self.examen, self.enunciado, self.calificacion)

    def consultar_respuestacorrecta(self):
        literal_correcto = Literal.objects.filter(status=True, pregunta=self, es_correcta=True)
        if literal_correcto.exists():
            return literal_correcto.first().texto
        return ''

    def cantidad_literales(self):
        return Literal.objects.filter(status=True, pregunta=self).count()

    def mis_literales(self):
        return Literal.objects.filter(status=True, pregunta=self)

    def es_respondida(self):
        return RespuestaAlumno.objects.filter(status=True, pregunta=self).exists()

class Literal(ModeloBase):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, blank=True, null=True)
    texto = models.CharField(max_length=255, blank=True, null=True)
    es_correcta = models.BooleanField(default=False, blank=True, null=True)

    def es_seleccionado(self):
        return RespuestaAlumno.objects.filter(status=True, pregunta=self.pregunta, respuesta_escogida=self).exists()

    def es_respuesta_correcta(self):
        respuesta = RespuestaAlumno.objects.filter(status=True, pregunta_id=self.pregunta, respuesta_escogida_id=self)
        if respuesta.exists():
            respuesta = respuesta.first()
            if respuesta.respuesta_escogida.es_correcta:
                return True
            else:
                return False
        return None


#ESTE MODELO ES UTILIZADO PARA INDICAR AL ESTUDIANTE LA RESPUESTA CORRECTA COMO NOTA EN COLOR VERDE
class Respuesta(ModeloBase):
    literal = models.ForeignKey(Literal, on_delete=models.CASCADE, blank=True, null=True)
    texto = models.CharField(max_length=255, blank=True, null=True)
    es_correcta = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return u'Enunciado: %s' % (self.texto)

class InscritosRecuperacionTest(ModeloBase):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, blank=True, null=True)
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return u'Examen :%s - Inscrito: %s' % (self.examen, self.inscrito)

class PreguntaAsignada(ModeloBase):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, blank=True, null=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, blank=True, null=True)
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.pregunta)

    class Meta:
        verbose_name = "Pregunta que se asigna aleatoriamente al inscrito"
        verbose_name_plural = "Preguntas que se asignan aleatoriamente al inscrito"
        ordering = ['id']


estado_examen = (
    (1, u'En proceso' ),
    (2, u'Finalizado')
)

class ExamenAlumno(ModeloBase):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, blank=True, null=True)
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.CASCADE, blank=True, null=True)
    estado = models.IntegerField(default=1, choices=estado_examen, blank=True, null=True, verbose_name=u'Estado del examen')
    fecha_inicio = models.DateTimeField(default=timezone.now, blank=True, null=True, verbose_name=u'Fecha que inicia el inscrito el examen')
    fecha_termina = models.DateTimeField(blank=True, null=True, verbose_name=u'Fecha que finaliza el inscrito el examen')
    calificacionfinal = models.FloatField(default=0, verbose_name=u'Calificación final del estudiante', blank=True, null=True)

    def __str__(self):
        return u'%s' % (self.examen)


class RespuestaAlumno(ModeloBase):
    examenalumno = models.ForeignKey(ExamenAlumno, on_delete=models.CASCADE, blank=True, null=True)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, blank=True, null=True)
    respuesta_escogida = models.ForeignKey(Literal, on_delete=models.CASCADE, blank=True, null=True)
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.CASCADE, blank=True, null=True)
    es_correcta = models.BooleanField(default=False, blank=True, null=True, verbose_name='El literal que escogió el participante es correcta o no?')
    calificacion = models.FloatField(default=0, verbose_name=u'Si el estudiante contestó correctamente la calificación será la misma de la pregunta', blank=True, null=True)

class NotaInscritoActividadA(ModeloBase):
    inscrito = models.ForeignKey(InscritoCursoA, on_delete=models.PROTECT, verbose_name=u'Inscrito que sube la tarea', blank=True, null=True)
    actividad = models.ForeignKey(DetalleActividadesModeloEvaluativoA, on_delete=models.PROTECT, verbose_name=u'La actividad que sube la tarea', blank=True, null=True)
    examen = models.ForeignKey(Examen, on_delete=models.PROTECT, verbose_name=u'Examen', blank=True, null=True)
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
