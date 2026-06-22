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

        if not self.jardin:
            errors["jardin"] = "La sala debe pertenecer a un jardín."

        if self.horario_inicio and self.horario_fin:
            if self.horario_fin <= self.horario_inicio:
                errors["horario_fin"] = (
                    "El horario de fin debe ser posterior al horario de inicio."
                )

        if self.responsable:
            if self.responsable.rol not in ["docente", "coordinador"]:
                errors["responsable"] = (
                    "El responsable de la sala debe tener rol 'docente' o 'coordinador'."
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
    Registro de asistencia diaria de los docentes en un Jardín específico.
    """
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
        related_name="asistencias_docentes"
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
        unique_together = ("docente", "jardin", "fecha")
        ordering = ["-fecha", "-hora_ingreso", "docente__last_name"]

    def clean(self):
        """Valida que la fecha no sea futura y que el usuario sea docente."""
        if self.fecha > timezone.now().date():
            raise ValidationError("No se puede registrar asistencia para una fecha futura.")
        
        if self.docente.rol != "docente":
            raise ValidationError("Solo se puede registrar asistencia para usuarios con el rol 'Docente'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.docente} - {self.jardin} - {self.fecha} ({self.get_estado_display()})"


def inicializar_asistencia_diaria(user, request=None):
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    ahora_local = timezone.localtime(timezone.now())
    hoy = ahora_local.date()
    hora = ahora_local.time()
    ip = request.META.get('REMOTE_ADDR') if request else None
    
    # Obtenemos los jardines asociados al docente a través de sus salas
    salas = user.salas_asignadas.all()
    jardines = Jardin.objects.filter(salas__in=salas).distinct()
    
    # Verificar si está fuera de jornada (comparamos con todas sus salas)
    es_fuera_de_jornada = True
    for sala in salas:
        # Margen de 30 minutos antes y después
        h_inicio = (datetime.combine(hoy, sala.horario_inicio) - timedelta(minutes=30)).time()
        h_fin = (datetime.combine(hoy, sala.horario_fin) + timedelta(minutes=30)).time()
        
        if h_inicio <= hora <= h_fin:
            es_fuera_de_jornada = False
            break
            
    # Check for active license
    licencia = LicenciaDocente.obtener_licencia_activa(user, hoy)
    if licencia:
        estado_inicial = 'L'
        obs_inicial = f"Ausente por licencia ({licencia.get_tipo_licencia_display()})."
    else:
        estado_inicial = 'A'
        obs_inicial = 'Registro inicializado por el sistema.'

    for jardin in jardines:
        # Usar update_or_create en lugar de get_or_create para mayor control
        asistencia, created = AsistenciaDocente.objects.update_or_create(
            docente=user,
            jardin=jardin,
            fecha=hoy,
            defaults={
                'hora_ingreso': None,
                'ip_address': ip,
                'fuera_de_jornada': es_fuera_de_jornada,
                'estado': estado_inicial,
                'fichado': False,  # Asegurar que está incluido
                'observaciones': obs_inicial
            }
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
        
        # Validar que docente y reemplazante no sean el mismo
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
