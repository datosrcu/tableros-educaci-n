"""
Modelos para la gestión jerárquica de la estructura educativa.
Define los Programas, Subprogramas, Espacios (Jardines) y Salas.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.utils import timezone

class Programa(models.Model):
    """
    Nivel superior de la organización (ej: Jardines Maternales, Apoyo Escolar).
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    usa_formulario_ampliado = models.BooleanField(
        default=False,
        help_text="Marca si este programa requiere el formulario ampliado de inscripción"
    )
    activo = models.BooleanField(default=True)
    prefijo_comprobante = models.CharField(
        max_length=10,
        default="BC",
        verbose_name="Prefijo Comprobante",
        help_text="Prefijo utilizado para generar los números de comprobantes (ej: EA, EC)"
    )

    
    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"

    def __str__(self):
        return self.nombre

class Subprograma(models.Model):
    """
    Subdivisión de un Programa para mayor granularidad administrativa.
    """
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='subprogramas'
    )
    nombre = models.CharField(max_length=100)
    
    usa_formulario_ampliado = models.BooleanField(
        default=False,
        help_text="Marca si este subprograma requiere formulario ampliado"
    )
    class Meta:
        verbose_name = "Subprograma"
        verbose_name_plural = "Subprogramas"
        unique_together = ("programa", "nombre")

    def __str__(self):
        return f"{self.programa} - {self.nombre}"


class Jardin(models.Model):
    """
    Representa un edificio físico o sede (Espacio) donde se dictan las clases.
    """
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="jardines",
        null=True,
        blank=True
    )
    
    subprograma = models.ForeignKey(
        Subprograma,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    SECTORES_CHOICES = [
        ('Norte', 'Norte'),
        ('Sur', 'Sur'),
        ('Este', 'Este'),
        ('Oeste', 'Oeste'),
        ('Centro', 'Centro'),
    ] 
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(max_length=150)
    coordenadas = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, choices=SECTORES_CHOICES)
    telefono = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Espacio"
        verbose_name_plural = "Espacios"
    
    def clean(self):
        """Valida la integridad de la jerarquía programa-subprograma."""
        if not self.programa:
            raise ValidationError("El espacio debe pertenecer a algún programa.")
        
        if self.subprograma and self.subprograma.programa != self.programa:
            raise ValidationError("El subprograma seleccionado no pertenece al programa del espacio.")
        
        if not self.direccion.strip():
            raise ValidationError("La dirección no puede estar vacía.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)    

    def __str__(self):
        return self.nombre

class AsignacionDocenteSala(models.Model):
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asignaciones_salas"
    )
    sala = models.ForeignKey(
        "Sala",
        on_delete=models.CASCADE,
        related_name="asignaciones_docentes"
    )
    lunes = models.BooleanField(default=True, verbose_name="Lunes")
    martes = models.BooleanField(default=True, verbose_name="Martes")
    miercoles = models.BooleanField(default=True, verbose_name="Miércoles")
    jueves = models.BooleanField(default=True, verbose_name="Jueves")
    viernes = models.BooleanField(default=True, verbose_name="Viernes")
    sabado = models.BooleanField(default=False, verbose_name="Sábado")
    domingo = models.BooleanField(default=False, verbose_name="Domingo")

    class Meta:
        unique_together = ("docente", "sala")
        verbose_name = "Asignación de Docente a Sala"
        verbose_name_plural = "Asignaciones de Docentes a Salas"

    def __str__(self):
        return f"{self.docente} en {self.sala}"

class Sala(models.Model):
    """
    Unidad educativa mínima dentro de un Jardín. 
    Vincula a los docentes con los alumnos y el horario.
    """
    jardin = models.ForeignKey(
        Jardin,
        on_delete=models.PROTECT,
        related_name="salas"
    )

    nombre = models.CharField(max_length=100)

    turno = models.CharField(
        max_length=20,
        choices=(
            ("mañana", "Mañana"),
            ("tarde", "Tarde"),
        )
    )

    horario_inicio = models.TimeField(default="08:00")
    horario_fin = models.TimeField(default="12:00")

    docentes = models.ManyToManyField(
        "users.Usuario",
        through="AsignacionDocenteSala",
        related_name="salas_asignadas",
        blank=True,
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salas_responsables",
    )

    subprograma = models.ForeignKey(
        "Subprograma",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salas",
        verbose_name="Subprograma"
    )

    # Días activos de la semana
    lunes = models.BooleanField(default=True, verbose_name="Lunes")
    martes = models.BooleanField(default=True, verbose_name="Martes")
    miercoles = models.BooleanField(default=True, verbose_name="Miércoles")
    jueves = models.BooleanField(default=True, verbose_name="Jueves")
    viernes = models.BooleanField(default=True, verbose_name="Viernes")
    sabado = models.BooleanField(default=False, verbose_name="Sábado")
    domingo = models.BooleanField(default=False, verbose_name="Domingo")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                "jardin",
                "turno",
                name="unique_sala_por_jardin_turno",
            )
        ]

    def clean(self):
        """Valida coherencia horaria y roles de los responsables."""
        super().clean()

        errors = {}

        if not self.jardin_id:
            errors["jardin"] = "La sala debe pertenecer a un jardín."

        if self.horario_inicio and self.horario_fin:
            if self.horario_fin <= self.horario_inicio:
                errors["horario_fin"] = (
                    "El horario de fin debe ser posterior al horario de inicio."
                )

        if self.responsable:
            if self.responsable.rol not in ["docente", "coordinador", "auxiliar"]:
                errors["responsable"] = (
                    "El responsable de la sala debe tener rol 'docente', 'coordinador' o 'auxiliar'."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.turno}) - {self.jardin}"
 


class AsistenciaDocente(models.Model):
    """
    Registro de asistencia diaria de los docentes en un Jardín/turno específico.
    La clave de unicidad es (docente, jardín, turno, fecha) para admitir
    que un mismo docente pueda tener dos fichadas en el mismo espacio si
    trabaja en distintos turnos.
    """
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
    ]

    ESTADO_CHOICES = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('J', 'Justificado'),
        ('T', 'Llegada Tarde'),
        ('R', 'Retiro Temprano'),
        ('L', 'Ausente por licencia'),
    ]
    
    docente = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="asistencias_docente"
    )
    jardin = models.ForeignKey(
        Jardin,
        on_delete=models.CASCADE,
        related_name="asistencias_docentes",
        null=True,
        blank=True,
        verbose_name="Espacio / Jardín"
    )
    # Turno al que corresponde este registro (null = registros históricos pre-migración)
    turno = models.CharField(
        max_length=20,
        choices=TURNO_CHOICES,
        null=True,
        blank=True,
        verbose_name="Turno"
    )
    fecha = models.DateField()
    hora_ingreso = models.TimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fuera_de_jornada = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='P')
    observaciones = models.TextField(blank=True, null=True)
    fichado = models.BooleanField(default=False, verbose_name="Fichado")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitud")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitud")

    # Usuario que registró la asistencia (null si fue automático)
    registrado_por = models.ForeignKey(
        "users.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asistencias_docentes_registradas"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asistencia de Docente"
        verbose_name_plural = "Asistencias de Docentes"
        # Nueva clave: docente + espacio + TURNO + fecha
        unique_together = ("docente", "jardin", "turno", "fecha")
        ordering = ["-fecha", "turno", "docente__last_name"]

    def clean(self):
        """Valida que la fecha no sea futura y que el usuario sea docente o auxiliar."""
        if self.fecha > timezone.now().date():
            raise ValidationError("No se puede registrar asistencia para una fecha futura.")
        
        if self.docente.rol not in ["docente", "auxiliar"]:
            raise ValidationError("Solo se puede registrar asistencia para usuarios con el rol 'Docente' o 'Auxiliar'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.docente} - {self.jardin} - {self.fecha} ({self.get_estado_display()})"


def _turno_por_hora(hora):
    """Determina el turno según la hora actual: antes de las 13:00 → mañana, después → tarde."""
    from datetime import time as dtime
    return 'mañana' if hora < dtime(13, 0) else 'tarde'


def inicializar_asistencia_diaria(user, request=None):
    """
    Crea los registros de AsistenciaDocente del día para el docente o auxiliar.
    - Para docentes con salas: un registro por cada combinación única (jardín, turno) en sus salas asignadas para el día de hoy.
    - Para auxiliares o personal sin salas: un único registro diario de asistencia.
    """
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    ahora_local = timezone.localtime(timezone.now())
    hoy = ahora_local.date()
    hora = ahora_local.time()
    ip = request.META.get('REMOTE_ADDR') if request else None
    
    dias_map = {
        0: 'lunes',
        1: 'martes',
        2: 'miercoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sabado',
        6: 'domingo'
    }
    dia_nombre = dias_map.get(hoy.weekday(), 'lunes')

    # Licencia activa
    licencia = LicenciaDocente.obtener_licencia_activa(user, hoy)
    if licencia:
        estado_inicial = 'L'
        obs_inicial = f"Ausente por licencia ({licencia.get_tipo_licencia_display()})."
    else:
        estado_inicial = 'A'
        obs_inicial = 'Registro inicializado por el sistema.'

    salas = user.salas_asignadas.select_related('jardin').all()

    if salas.exists():
        # Mapa de asignaciones de días específicos del docente por sala
        from .models import AsignacionDocenteSala
        asignaciones_map = {
            asig.sala_id: asig
            for asig in AsignacionDocenteSala.objects.filter(docente=user)
        }

        pares_vistos = set()
        for sala in salas:
            asig = asignaciones_map.get(sala.id)
            # Si el docente no tiene habilitado este día de la semana para la sala, omitir
            if asig and not getattr(asig, dia_nombre, True):
                continue
            # Si la sala en sí no funciona hoy, omitir
            if not getattr(sala, dia_nombre, True):
                continue

            par = (sala.jardin_id, sala.turno)
            if par in pares_vistos:
                continue
            pares_vistos.add(par)

            jardin = sala.jardin
            turno = sala.turno  # 'mañana' o 'tarde'

            if AsistenciaDocente.objects.filter(
                docente=user, jardin=jardin, turno=turno, fecha=hoy
            ).exists():
                continue

            if sala.horario_inicio and sala.horario_fin:
                h_inicio = (datetime.combine(hoy, sala.horario_inicio) - timedelta(minutes=30)).time()
                h_fin = (datetime.combine(hoy, sala.horario_fin) + timedelta(minutes=30)).time()
                fuera = not (h_inicio <= hora <= h_fin)
            else:
                fuera = False

            AsistenciaDocente.objects.create(
                docente=user,
                jardin=jardin,
                turno=turno,
                fecha=hoy,
                hora_ingreso=None,
                ip_address=ip,
                fuera_de_jornada=fuera,
                estado=estado_inicial,
                fichado=False,
                observaciones=obs_inicial
            )

        # Si tras filtrar por día no se creó ninguna ficha porque todas son de otros días,
        # pero el docente intentara fichar, dejamos que else maneje auxiliares o que se inicialice al fichar.
    else:
        # Para Auxiliares o personal sin salas asignadas: 1 solo registro de asistencia diaria
        if not AsistenciaDocente.objects.filter(docente=user, fecha=hoy).exists():
            target_jardin = None
            if user.programas_asignados.exists():
                target_jardin = Jardin.objects.filter(programa__in=user.programas_asignados.all()).first()
            if not target_jardin:
                target_jardin = Jardin.objects.first()

            AsistenciaDocente.objects.create(
                docente=user,
                jardin=target_jardin,
                turno=None,
                fecha=hoy,
                hora_ingreso=None,
                ip_address=ip,
                fuera_de_jornada=False,
                estado=estado_inicial,
                fichado=False,
                observaciones="Registro de asistencia de auxiliar."
            )


class LicenciaDocente(models.Model):
    TIPO_CHOICES = [
        ('enfermedad', 'Enfermedad'),
        ('maternidad_paternidad', 'Maternidad / Paternidad'),
        ('familiar_cargo', 'Familiar a cargo'),
        ('estudio_capacitacion', 'Estudio y capacitación'),
        ('razones_particulares', 'Razones particulares'),
        ('duelo', 'Duelo'),
        ('matrimonio', 'Matrimonio'),
        ('sangre_organos', 'Donación de sangre u órganos'),
        ('gremial', 'Gremial'),
        ('otro', 'Otro'),
    ]

    docente = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="licencias",
        verbose_name="Docente"
    )
    tipo_licencia = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de licencia"
    )
    motivo = models.TextField(
        verbose_name="Motivo / Descripción"
    )
    fecha_desde = models.DateField(
        verbose_name="Fecha desde"
    )
    fecha_hasta = models.DateField(
        verbose_name="Fecha hasta"
    )
    reemplazante = models.ForeignKey(
        "users.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reemplazos",
        verbose_name="Docente reemplazante"
    )
    creado_por = models.ForeignKey(
        "users.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="licencias_creadas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Licencia de Docente"
        verbose_name_plural = "Licencias de Docentes"
        ordering = ["-fecha_desde", "docente__last_name"]

    def clean(self):
        super().clean()
        if self.fecha_desde and self.fecha_hasta:
            if self.fecha_hasta < self.fecha_desde:
                raise ValidationError({
                    "fecha_hasta": "La fecha hasta debe ser posterior o igual a la fecha desde."
                })
        
        if self.docente and self.reemplazante and self.docente == self.reemplazante:
            raise ValidationError({
                "reemplazante": "El docente reemplazante no puede ser la misma persona con licencia."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def obtener_licencia_activa(cls, docente, fecha):
        return cls.objects.filter(
            docente=docente,
            fecha_desde__lte=fecha,
            fecha_hasta__gte=fecha
        ).first()

    def __str__(self):
        return f"Licencia de {self.docente} ({self.fecha_desde} al {self.fecha_hasta})"