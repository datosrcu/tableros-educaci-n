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
