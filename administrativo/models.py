from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Sum
import datetime
from datetime import datetime

from administrativo.funciones import *
from academia.models import *


def generar_secuencial_factura():
    secuencial = Secuencial.objects.filter(status=True)
    if secuencial:
        secuencial = secuencial.last()
        secuencial.factura = secuencial.factura + 1
        secuencial.save()
    else:
        secuencial = Secuencial(factura=0)
        secuencial.save()
    return secuencial.factura


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
    cedula = models.CharField(max_length=10, verbose_name=u'Cédula', null=True, blank=True)
    telefono_movil = models.CharField(max_length=10, verbose_name=u"Teléfono móvil", null=True, blank=True)
    telefono_convencional = models.CharField(max_length=10, verbose_name=u"Teléfono convencional", null=True,
                                             blank=True)
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

    def totalrubros(self):
        total = Rubro.objects.filter(persona_id=self.id, status=True).aggregate(total=Sum('valor'))
        if not total['total']:
            return 0.00
        return total['total']

    def totalpagos(self):
        lista_rubros = Rubro.objects.filter(persona_id=self.id, status=True).values_list('id')
        total = Pago.objects.filter(rubro_id__in=lista_rubros, status=True).aggregate(total=Sum('valorfinal'))
        valorpago = 0.00
        if total['total']:
            valorpago = total['total']
        return solo_2_decimales(valorpago, 2)

    def calcular_porcentaje(self):
        total = Rubro.objects.filter(persona_id=self.id, status=True).aggregate(total=Sum('valor'))
        rubrototal = total['total'] if total['total'] else 0
        ciento = 100
        resultado = solo_2_decimales(rubrototal / ciento, 2)
        lista_rubros = Rubro.objects.filter(persona_id=self.id, status=True).values_list('id')
        total = Pago.objects.filter(rubro_id__in=lista_rubros, status=True).aggregate(total=Sum('valorfinal'))
        totalpagado = total['total'] if total['total'] else 0
        valorporcentaje = solo_2_decimales(totalpagado / resultado, 2)
        return valorporcentaje

    def verificar_estadocuenta(self):
        lista_rubros = Rubro.objects.filter(persona=self, cancelado=False, status=True)
        tienevalorapagar = False
        if lista_rubros:
            tienevalorapagar = True
        return tienevalorapagar


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
        return self.is_profesor

    def es_administrador(self):
        return self.is_administrador

    def es_alumno(self):
        return self.is_alumno


class Cargo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Cargo"
        verbose_name_plural = u" Cargos"
        ordering = ['nombre']


class Docente(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, null=True, blank=True)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    contrato = models.CharField(default='', max_length=50, null=True, blank=True, verbose_name=u"Contrato")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.persona

    def en_uso(self):
        return Curso.objects.filter(status=True, docente=self).exists()


class Alumno(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % self.persona

    def totalrubros(self):
        total = Rubro.objects.filter(persona_id=self.persona.id, status=True).aggregate(total=Sum('valor'))
        if not total['total']:
            return 0.00
        return total['total']

    def totalpagos(self):
        lista_rubros = Rubro.objects.filter(persona_id=self.persona.id, status=True).values_list('id')
        total = Pago.objects.filter(rubro_id__in=lista_rubros, status=True).aggregate(total=Sum('valorfinal'))
        valorpago = 0.00
        if total['total']:
            valorpago = total['total']
        return ("{0:.0f}".format(valorpago))

    def verificar_estadocuenta(self):
        lista_rubros = Rubro.objects.filter(persona_id=self.persona.id, cancelado=False, status=True)
        tienevalorapagar = False
        if lista_rubros:
            tienevalorapagar = True
        return tienevalorapagar

    def en_uso(self):
        return InscritoCurso.objects.filter(status=True, alumno=self).exists()


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
    finalizado = models.BooleanField(default=False, verbose_name=u"Finalizado")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Modelo evaluativo"
        verbose_name_plural = u"Modelos evaluativos"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(ModeloEvaluativo, self).save(*args, **kwargs)

    def tiene_cursos_vinculados(self):
        return Curso.objects.filter(status=True, modeloevaluativo=self).exists()

    def tiene_detalle_modelo(self):
        return DetalleModeloEvaluativo.objects.filter(status=True, modelo=self).exists()


class DetalleModeloEvaluativo(ModeloBase):
    modelo = models.ForeignKey(ModeloEvaluativo, on_delete=models.PROTECT, verbose_name=u"Modelo")
    nombre = models.CharField(default='', max_length=200, verbose_name=u"Nombre campo")
    notaminima = models.FloatField(default=0, verbose_name=u'Nota minima')
    notamaxima = models.FloatField(default=0, verbose_name=u'Nota maxima')
    orden = models.IntegerField(default=0, verbose_name=u"Orden en acta")

    def __str__(self):
        return u'%s (%s a %s)' % (self.nombre, self.notaminima.__str__(), self.notamaxima.__str__())

    class Meta:
        verbose_name = u"Detalle del modelo evaluativo"
        verbose_name_plural = u"Detalles de los modelos evaluativos"
        ordering = ['orden']

    def importarmodelo(self, curso_id):
        cursoadm = Curso.objects.get(id=int(curso_id))
        cursoacad = CursoA.objects.get(id=cursoadm.idcursoacademia_id)
        modeloevaluativo = cursoacad.modeloevaluativo
        detallemodeloacad = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=modeloevaluativo,
                                                                    nombre=self.nombre)
        if detallemodeloacad:
            return detallemodeloacad.first().nombre
        return '---'

    def extraernotaadm(self, inscrito_id):
        try:
            nota = NotaInscrito.objects.filter(status=True, inscrito_id=inscrito_id, modelo=self)
            if nota:
                return nota.first().notafinal
            return 0.00
        except Exception as ex:
            pass

    def extraernotaacad(self, curso_id, persona_id):
        cursoadm = Curso.objects.get(id=int(curso_id))
        cursoacad = CursoA.objects.get(id=cursoadm.idcursoacademia_id)
        modeloevaluativo = cursoacad.modeloevaluativo
        detallemodeloacad = DetalleModeloEvaluativoA.objects.filter(status=True, modelo=modeloevaluativo,
                                                                    nombre=self.nombre)
        inscritoacad = InscritoCursoA.objects.get(status=True, curso=cursoacad, inscrito_id=persona_id)
        if detallemodeloacad:
            detalleactividad = lista_actividades = conteo = DetalleActividadesModeloEvaluativoA.objects.filter(status=True, detalle=detallemodeloacad.first())
            lista_actividades = lista_actividades.values_list('id')
            conteo = conteo.count()
            totalnotas = NotaInscritoActividadA.objects.filter(status=True, actividad_id__in=detalleactividad, inscrito=inscritoacad).aggregate(total=Sum('nota'))
            totalnotas = totalnotas['total'] if totalnotas['total'] else 0
            if conteo > 0 and totalnotas:
                resultado = totalnotas / conteo
            else:
                resultado = 0
            return resultado
        return 0


class Documentos(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, blank=True, null=True)
    archivo = models.FileField(upload_to='documentos', blank=True, null=True, verbose_name=u'Documentos')
    nombre = models.CharField(max_length=500, null=True)


class Curso(ModeloBase):
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT, verbose_name=u'Periodo', blank=True, null=True)
    modeloevaluativo = models.ForeignKey(ModeloEvaluativo, on_delete=models.PROTECT, verbose_name=u'Modelo Evaluativo',
                                         blank=True, null=True)
    idcursoacademia = models.ForeignKey(CursoA, on_delete=models.PROTECT, verbose_name=u'Curso académico', blank=True,
                                        null=True)
    nombre = models.CharField(max_length=500, verbose_name=u'Nombre')
    estado = models.IntegerField(default=2, choices=ESTADO_CURSO, blank=True, null=True, verbose_name=u'Estado Curso')
    tiporubro = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para cuota",
                                  on_delete=models.PROTECT, blank=True, null=True)
    tiporubroinscripcion = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para inscripcion",
                                             on_delete=models.PROTECT, blank=True, null=True)
    tiporubromatricula = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para matricula",
                                           on_delete=models.PROTECT, blank=True, null=True)
    tiporubrocuota = models.ForeignKey(TipoOtroRubro, related_name='+', verbose_name=u"Rubro para cuotas",
                                       on_delete=models.PROTECT, blank=True, null=True)
    horasvirtual = models.IntegerField(default=0, verbose_name=u'Horas Virtuales')
    minasistencia = models.IntegerField(default=0, verbose_name=u'Asistencia mínima para aprobar')
    minnota = models.IntegerField(default=0, verbose_name=u'Nota mínima para aprobar')
    cupo = models.IntegerField(default=0, verbose_name=u'Cupo')
    cuotas = models.IntegerField(default=0, verbose_name=u'Cuotas')
    costo = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u"Costo del curso")
    gcuotas = models.BooleanField(default=False, verbose_name=u"El curso genera cuotas?")
    inscripcion = models.BooleanField(default=False, verbose_name=u"El curso aplica inscripción?")
    costoinscripcion = models.DecimalField(max_digits=30, decimal_places=2, default=0,
                                           verbose_name=u"Costo de la inscripción")
    oferta = models.BooleanField(default=False, verbose_name=u"Aplica oferta?")
    costooferta = models.DecimalField(max_digits=30, decimal_places=2, default=0,
                                      verbose_name=u"Costo del curso aplicando oferta")
    matricula = models.BooleanField(default=False, verbose_name=u"Matrícula")
    costomatricula = models.DecimalField(max_digits=30, decimal_places=2, default=0,
                                         verbose_name=u"Costo de la matrícula")
    modalidad = models.IntegerField(default=1, choices=MODALIDAD_CAPACITACION, blank=True, null=True,
                                    verbose_name=u'Modalidad DEL CURSO')
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
    planificacion = models.FileField(upload_to='planificacioncurso', verbose_name='Planificación', null=True,
                                     blank=True)
    fondoweb = models.ImageField(verbose_name="Fondo para página web", upload_to='fondoweb', null=True, blank=True)
    fondocursos = models.ImageField(verbose_name="Fondo para cursos", upload_to='fondocursos', null=True, blank=True)
    migrado = models.BooleanField(default=False, blank=True, null=True)
    finalizarcurso = models.BooleanField(default=False, verbose_name='¿Curso terminado?', null=True, blank=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.nombre)

    def mimodeloevaluativo(self):
        return DetalleModeloEvaluativo.objects.filter(status=True, modelo=self.modeloevaluativo)

    def total_inscritos(self):
        return InscritoCurso.objects.filter(status=True, curso=self).count()

    def estado_curso(self):
        if self.estado == 1 or self.estado == 2:
            return 'success'
        else:
            return 'danger'


ESTADO_ATENCION = (
    (1, u'ATENDIDO'),
    (2, u'PENDIENTE'),
)


class Lead(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, blank=True, null=True)
    atendido = models.IntegerField(default=2, choices=ESTADO_ATENCION, blank=True, null=True,
                                   verbose_name=u'Campo para verificar si el interesado fue atendido o no')

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-id']

    def __str__(self):
        return u'%s' % self.persona


ESTADO_INSCRITO = (
    (1, u'APROBADO'),
    (2, u'REPROBADO'),
    (3, u'RETIRADO'),
)


class InscritoCurso(ModeloBase):
    alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT, verbose_name=u"Alumno")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, verbose_name=u"Curso")
    estado = models.IntegerField(default=2, choices=ESTADO_INSCRITO, blank=True, null=True, verbose_name=u'Modalidad DEL CURSO')
    notafinal = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Nota final')
    matriculado = models.BooleanField(default=False, blank=True, null=True)
    iduseracad = models.ForeignKey('academia.InscritoCursoA', on_delete=models.PROTECT, verbose_name=u"Inscrito academia", blank=True, null=True)

    class Meta:
        verbose_name = "Inscrito Curso"
        verbose_name_plural = "Inscritos por curso"
        ordering = ['id']

    def __str__(self):
        return u'%s' % (self.alumno)

    def adeuda(self):
        curso = self.curso
        rubros = Rubro.objects.filter(status=True, persona=self.alumno.persona, curso=curso).values_list('id', flat=True)
        totalpagos = Pago.objects.filter(rubro_id__in=rubros, status=True).aggregate(total=Sum('valorfinal'))
        if totalpagos['total']:
            saldofinal = float(totalpagos['total'])
            if float(curso.costo) == saldofinal:
                return True
        return False

    def puede_eliminar_inscrito(self):
        curso = self.curso
        rubros = Rubro.objects.filter(status=True, persona=self.alumno.persona, curso=curso).values_list('id', flat=True)
        totalpagos = Pago.objects.filter(rubro_id__in=rubros, status=True).count()
        if totalpagos > 0:
            return False
        return True


    def estado_aprobacion(self):
        if self.estado == 1:
            return 'success'
        else:
            return 'danger'

    def generar_rubros(self, curso):
        try:
            if not curso.oferta:
                if curso.inscripcion:
                    rubroinscripcion = Rubro(nombre=curso.tiporubroinscripcion.nombre + ' - ' + curso.nombre,
                                             tiporubro=curso.tiporubroinscripcion, curso=curso,
                                             persona=self.alumno.persona, tipocuota=1, valor=curso.costoinscripcion,
                                             fecha=datetime.now().date(), cancelado=False, saldo=curso.costoinscripcion)
                    rubroinscripcion.save()

                if curso.matricula:
                    rubromatricula = Rubro(nombre=curso.tiporubromatricula.nombre + ' - ' + curso.nombre,
                                           tiporubro=curso.tiporubromatricula, curso=curso, persona=self.alumno.persona,
                                           tipocuota=2, valor=curso.costomatricula,
                                           fecha=datetime.now().date(), cancelado=False, saldo=curso.costomatricula)
                    rubromatricula.save()

                if curso.gcuotas:
                    cuotas = CuotasCurso.objects.filter(status=True, curso=curso)
                    for cuota in cuotas:
                        rubrocuotas = Rubro(nombre=curso.tiporubrocuota.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubrocuota, curso=curso, persona=self.alumno.persona,
                                            cuota=cuota.numerocuota, tipocuota=3, valor=cuota.valor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=curso.valor)
                        rubrocuotas.save()

                if not curso.inscripcion and not curso.matricula and not curso.gcuotas:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=curso.costo,
                                            fecha=datetime.now().date(), cancelado=False, saldo=curso.costo)
                    nuevorubrocurso.save()

                if curso.inscripcion and not curso.matricula and not curso.gcuotas:
                    diferenciavalor = solo_2_decimales(curso.costo - curso.costoinscripcion, 2)
                    # if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=diferenciavalor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=diferenciavalor)
                    nuevorubrocurso.save()

                if not curso.inscripcion and curso.matricula and not curso.gcuotas:
                    diferenciavalor = solo_2_decimales(curso.costo - curso.costomatricula, 2)
                    # if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=diferenciavalor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=diferenciavalor)
                    nuevorubrocurso.save()

            else:
                if curso.inscripcion:
                    rubroinscripcion = Rubro(nombre=curso.tiporubroinscripcion.nombre + ' - ' + curso.nombre,
                                             tiporubro=curso.tiporubroinscripcion, curso=curso,
                                             persona=self.alumno.persona, tipocuota=1, valor=curso.costoinscripcion,
                                             fecha=datetime.now().date(), cancelado=False, saldo=curso.costoinscripcion)
                    rubroinscripcion.save()

                if curso.matricula:
                    rubromatricula = Rubro(nombre=curso.tiporubromatricula.nombre + ' - ' + curso.nombre,
                                           tiporubro=curso.tiporubromatricula, curso=curso, persona=self.alumno.persona,
                                           tipocuota=2, valor=curso.costomatricula,
                                           fecha=datetime.now().date(), cancelado=False, saldo=curso.costomatricula)
                    rubromatricula.save()

                if curso.gcuotas:
                    cuotas = CuotasCurso.objects.filter(status=True, curso=curso)
                    for cuota in cuotas:
                        rubrocuotas = Rubro(nombre=curso.tiporubrocuota.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubrocuota, curso=curso, persona=self.alumno.persona,
                                            cuota=cuota.numerocuota, tipocuota=3, valor=cuota.valor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=curso.valor)
                        rubrocuotas.save()

                if not curso.inscripcion and not curso.matricula and not curso.gcuotas:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=curso.costooferta,
                                            fecha=datetime.now().date(), cancelado=False, saldo=curso.costooferta)
                    nuevorubrocurso.save()

                if curso.inscripcion and not curso.matricula and not curso.gcuotas:
                    diferenciavalor = solo_2_decimales(curso.costooferta - curso.costoinscripcion, 2)
                    # if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=diferenciavalor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=diferenciavalor)
                    nuevorubrocurso.save()

                if not curso.inscripcion and curso.matricula and not curso.gcuotas:
                    diferenciavalor = solo_2_decimales(curso.costooferta - curso.costomatricula, 2)
                    # if diferenciavalor:
                    nuevorubrocurso = Rubro(nombre=curso.tiporubro.nombre + ' - ' + curso.nombre,
                                            tiporubro=curso.tiporubro, curso=curso, persona=self.alumno.persona,
                                            tipocuota=4,
                                            valor=diferenciavalor,
                                            fecha=datetime.now().date(), cancelado=False, saldo=diferenciavalor)
                    nuevorubrocurso.save()

            return True
        except Exception as ex:
            return False

    def calcularpromedio(self, curso_id):
        cursoadm = Curso.objects.get(id=int(curso_id))
        modeloadm = cursoadm.modeloevaluativo
        detalles = DetalleModeloEvaluativo.objects.filter(status=True, modelo=modeloadm)
        conteo = detalles.count()
        sumnotas = 0
        for detalle in detalles:
            totalnota = NotaInscrito.objects.filter(status=True, modelo=detalle, inscrito=self).aggregate(total=Sum('notafinal'))
            if totalnota['total']:
                sumnotas += totalnota['total']

        if conteo > 0 and sumnotas:
            resultado = sumnotas / conteo
        else:
            resultado = 0
        return resultado


class NotaInscrito(ModeloBase):
    inscrito = models.ForeignKey(InscritoCurso, on_delete=models.PROTECT, verbose_name=u"Alumno")
    modelo = models.ForeignKey(DetalleModeloEvaluativo, on_delete=models.PROTECT,
                               verbose_name=u"Modelo Evaluativo: N1, N2, N3, etc.")
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
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    nombre = models.CharField(max_length=300, blank=True, null=True)
    cuota = models.IntegerField(default=0, verbose_name=u'Cuota')
    tipocuota = models.IntegerField(choices=TIPO_CUOTA, default=3)
    subtotal = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Subtotal')
    valor = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Valor')
    saldo = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Saldo')
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)
    fechavencimiento = models.DateField(verbose_name=u'Fecha vencimiento', auto_now_add=True, null=True)
    cancelado = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return u'%s - Valor: %s' % (self.nombre, self.valor)

    def nombrecurso(self):
        return u'%s' % (self.curso)

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


class CuotasCurso(ModeloBase):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, verbose_name=u'Curso', blank=True, null=True)
    numerocuota = models.IntegerField(default=0, verbose_name=u'Número de la cuota', blank=True, null=True)
    inicio = models.DateField(verbose_name=u'Fecha inicio', blank=True, null=True)
    fin = models.DateField(verbose_name=u'Fecha fin', blank=True, null=True)
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor de la cuota')


class AccesoModulo(ModeloBase):
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Acceso a módulo"
        verbose_name_plural = "Acceso a módulos"
        ordering = ['id']

    def __str__(self):
        return u'%s - %s - %s' % (self.grupo, self.modulo, self.activo)


class TiempoAntesRecordatorioCorreo(ModeloBase):
    dias_antes = models.CharField(max_length=100, verbose_name=u'Días antes del recordatorio')
    horas_antes = models.CharField(max_length=100, verbose_name=u'Horas antes del recordatorio')
    minutos_antes = models.CharField(max_length=100, verbose_name=u'Minutos antes del recordatorio')

    def __str__(self):
        return u'Días: %s | Horas: %s | Minutos: %s' % (self.dias_antes, self.horas_antes, self.minutos_antes)


class Caja(ModeloBase):
    nombre = models.CharField(verbose_name="Nombre de la caja", max_length=100, unique=True)
    descripcion = models.CharField(verbose_name="Descripción de la caja", default='', max_length=200)
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, verbose_name=u'Persona encarga de la caja',
                                blank=True, null=True)
    activo = models.BooleanField(verbose_name="¿Caja activa?")

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['id']

    def __str__(self):
        return u'%s - %s' % (self.nombre, self.persona)

    def estado_caja(self):
        return 'success' if self.activo else 'danger'


class SesionCaja(ModeloBase):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, verbose_name=u'Caja a aperturar', blank=True, null=True)
    inicio = models.DateField(verbose_name=u'Fecha inicio')
    fin = models.DateField(verbose_name=u'Fecha fin')
    valorinicial = models.DecimalField(default=0, max_digits=30, decimal_places=2,
                                       verbose_name=u'Valor con el que comienza la caja')
    activo = models.BooleanField(default=True, verbose_name=u'Sesión activa')

    class Meta:
        verbose_name = "Sesion Caja"
        verbose_name_plural = "Sesiones de caja"
        ordering = ['id']

    def __str__(self):
        return u'%s: %s - %s' % (self.caja, self.inicio, self.fin)

    def estado_sesioncaja(self):
        return 'success' if self.activo else 'danger'

    def totalfacturado(self):
        total = Factura.objects.filter(sesioncaja=self, status=True).aggregate(total=Sum('total'))
        return total['total'] if total['total'] else 0


class CierreSesionCaja(ModeloBase):
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u'Sesión caja', blank=True,
                                   null=True)
    fechacierre = models.DateField(verbose_name=u'Fecha fin')
    totalfacturado = models.DecimalField(default=0, max_digits=30, decimal_places=2,
                                         verbose_name=u'Valor con el que cierra la caja')

    class Meta:
        verbose_name = "Cierre Sesion Caja"
        verbose_name_plural = "Cierres de sesiones de caja"
        ordering = ['id']

    def __str__(self):
        return u'%s: %s - %s' % (self.sesioncaja, self.fechacierre, self.totalfacturado)


class ValorRecaudado(ModeloBase):
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u'Sesión caja', blank=True,
                                   null=True)
    rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT, verbose_name=u'Rubro facturado', blank=True, null=True)
    valor = models.DecimalField(max_digits=30, decimal_places=2, default=0, verbose_name=u'Valor recaudado')

    class Meta:
        verbose_name = "Valor recaudado en la sesión de caja"
        verbose_name_plural = "Valores recaudados en las sesiones de caja"
        ordering = ['id']

    def __str__(self):
        return u'%s - %s - %s' % (self.sesioncaja, self.rubro, self.valor)


ESTADO_PAGO = (
    (1, u'VALIDADO'),
    (2, u'ANULADO'),
)


class Pago(ModeloBase):
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.CASCADE, blank=True, null=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    rubro = models.ForeignKey(Rubro, on_delete=models.CASCADE)
    valor = models.FloatField(default=0, verbose_name=u'Pago')
    iva = models.DecimalField(max_digits=30, decimal_places=2, default=12, verbose_name=u'Iva')
    subtotal_iva = models.FloatField(default=0, verbose_name=u'Subtotal iva')
    valorfinal = models.FloatField(default=0, verbose_name=u'Valor final')
    fecha = models.DateField(verbose_name=u'Fecha', auto_now_add=True, null=True)
    estado = models.IntegerField(choices=ESTADO_PAGO, default=1, verbose_name=u"Validado o anulado", blank=True,
                                 null=True)

    def factura(self):
        factura = DetalleFactura.objects.filter(status=True, pago=self)
        if factura:
            numerocompleto = ''
            factura = str(factura.first().factura.numero)
            if len(factura) == 1:
                numerocompleto = '001-001-000' + str(factura)
            elif len(factura) == 2:
                numerocompleto = '001-001-00' + str(factura)
            elif len(factura) == 3:
                numerocompleto = '001-001-0' + str(factura)
            elif len(factura) == 4:
                numerocompleto = '001-001-' + str(factura)
            return numerocompleto
        return ''


IDENTIFICACIONES = (
    (1, u'CEDULA'),
    (2, u'RUC'),
)

IVA = (
    (1, 0),
    (2, 12),
    (3, 14),
)

PROCESO_COMPROBANTE = (
    (1, u'PENDIENTE'),
    (2, u'FINALIZADA')
)


class Secuencial(ModeloBase):
    factura = models.IntegerField(default=0, verbose_name=u'Secuencial de facturas')


class Factura(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, blank=True, null=True)
    archivo = models.FileField(upload_to='facturas', blank=True, null=True, verbose_name=u'Facturas')
    numero = models.IntegerField(default=0, verbose_name=u"Numero", blank=True, null=True)
    numerocompleto = models.CharField(default='', max_length=20, verbose_name=u"Numero Completo", blank=True, null=True)
    fecha = models.DateField(verbose_name=u"Fecha", blank=True, null=True)
    observacion = models.TextField(default='', blank=True, null=True, verbose_name=u'Observación')
    valida = models.BooleanField(default=True, verbose_name=u"Valida", blank=True, null=True)
    ivaaplicado = models.IntegerField(choices=IVA, default=2, verbose_name=u"Tipo de iva", blank=True, null=True)
    subtotal_base_iva = models.DecimalField(max_digits=30, decimal_places=2, default=0, blank=True, null=True)
    subtotal_base0 = models.DecimalField(max_digits=30, decimal_places=2, default=0, blank=True, null=True)
    total_descuento = models.DecimalField(max_digits=30, decimal_places=2, default=0, blank=True, null=True)
    total_iva = models.DecimalField(max_digits=30, decimal_places=2, default=0, blank=True, null=True)
    total = models.DecimalField(max_digits=30, decimal_places=2, default=0, blank=True, null=True)
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u"Caja", blank=True, null=True)
    identificacion = models.CharField(default='', max_length=20, verbose_name=u"Identificación", blank=True, null=True)
    tipo = models.IntegerField(choices=IDENTIFICACIONES, default=1, verbose_name=u"Tipo de identificación", blank=True,
                               null=True)
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre", blank=True, null=True)
    email = models.CharField(default='', max_length=100, verbose_name=u"Email", blank=True, null=True)
    direccion = models.TextField(default='', verbose_name=u"Dirección", blank=True, null=True)
    telefono = models.CharField(default='', max_length=50, verbose_name=u"Telefono", blank=True, null=True)
    electronica = models.BooleanField(default=False, verbose_name=u"Electrónica", blank=True, null=True)
    pagada = models.BooleanField(default=True, verbose_name=u"Pagada", blank=True, null=True)
    firmada = models.BooleanField(default=False, verbose_name=u"Firmada", blank=True, null=True)
    enviadasri = models.BooleanField(default=False, verbose_name=u"Enviada al sri", blank=True, null=True)
    falloenviodasri = models.BooleanField(default=False, verbose_name=u"Fallo existente al enviar la factura al sri",
                                          blank=True, null=True)
    mensajeenvio = models.TextField(blank=True, null=True, verbose_name=u"Mensaje de envio por parte del sri")
    falloautorizacionsri = models.BooleanField(default=False, verbose_name=u"Fallo de Autorización SRI", blank=True,
                                               null=True)
    mensajeautorizacion = models.TextField(blank=True, null=True, verbose_name=u"Mensaje de Autorización")
    autorizada = models.BooleanField(default=False, verbose_name=u"Autorizada", blank=True, null=True)
    enviadacliente = models.BooleanField(default=False, verbose_name=u"Enviada por correo", blank=True, null=True)
    xmlgenerado = models.BooleanField(default=False, verbose_name=u"XML Generado", blank=True, null=True)
    xml = models.TextField(blank=True, null=True, verbose_name=u'XML')
    xmlfirmado = models.TextField(blank=True, null=True, verbose_name=u'XML Firmado')
    xmlarchivo = models.FileField(upload_to='comprobantes/facturas/', blank=True, null=True,
                                  verbose_name=u'XML Archivo')
    fechaautorizacion = models.DateTimeField(verbose_name=u"Fecha autorizacion", blank=True, null=True)
    autorizacion = models.TextField(verbose_name=u'Autorizacion', blank=True, null=True)
    weburl = models.CharField(max_length=32, blank=True, null=True)
    claveacceso = models.CharField(max_length=49, verbose_name=u'Clave de Acceso', blank=True, null=True)
    tipoambiente = models.IntegerField(default=1, verbose_name=u'Tipo Ambiente', blank=True, null=True)
    tipoemision = models.IntegerField(default=1, verbose_name=u'Tipo Emision', blank=True, null=True)
    estado = models.IntegerField(choices=PROCESO_COMPROBANTE, default=1, verbose_name=u'Estado de la factura',
                                 blank=True, null=True)
    aplicanc = models.BooleanField(default=False, verbose_name=u"Aplica nota de crédito", blank=True, null=True)

    def __str__(self):
        return u'Factura No. %s' % self.numero

    class Meta:
        verbose_name = u"Factura"
        verbose_name_plural = u"Facturas"
        ordering = ['numero']
        unique_together = ('numero',)


class DetalleFactura(ModeloBase):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, blank=True, null=True)
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, blank=True, null=True)
