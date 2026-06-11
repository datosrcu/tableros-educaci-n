"""
Modelos para la gestión de alumnos, inscripciones, asistencias y tutores.
Este módulo define la estructura de datos central para el registro de estudiantes
y el seguimiento de su ciclo escolar.
"""
from django.db import models
from jardines.models import Sala
from users.models import Usuario
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

class Alumno(models.Model):
    """
    Representa a un estudiante inscripto en el sistema.
    Mantiene información personal básica, estado de actividad y vinculación a una sala.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, help_text="DNI sin puntos ni espacios.")
    fecha_nacimiento = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    tutores = models.ManyToManyField("Tutor", related_name="alumnos", blank=True, help_text="Responsables legales o tutores.")

    def clean(self):
        """
        Validaciones de integridad de datos para el Alumno.
        - Verifica que el DNI sea numérico.
        - Valida que la edad esté en el rango permitido.
        - Asegura la consistencia entre el estado activo y la fecha de baja.
        """
        # 🔹 DNI solo números
        if not self.dni.isdigit():
            raise ValidationError({"dni": "El DNI debe contener solo números."})

        # 🔹 Edad razonable (desde 45 días hasta 100 años para incluir talleres de adultos)
        dias_vividos = (date.today() - self.fecha_nacimiento).days
        edad_anios = dias_vividos / 365.25
        if edad_anios < 0.12 or edad_anios > 100:
            raise ValidationError({
                "fecha_nacimiento": "La edad del alumno no es válida para este sistema (debe tener entre 45 días y 100 años)."
            })

    def save(self, *args, **kwargs):
        """Sobreescritura para forzar la limpieza de datos antes de guardar."""
        self.full_clean()  # 🔥 fuerza validaciones siempre
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

class AsignacionSala(models.Model):
    """
    Registra el vínculo entre un alumno y una sala particular.
    Soporta múltiples inscripciones para un mismo alumno (ej: doble turno).
    """
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="asignaciones")
    sala = models.ForeignKey("jardines.Sala", on_delete=models.PROTECT, related_name="alumnos_asignados")
    activo = models.BooleanField(default=True, help_text="Indica si el alumno sigue cursando en esta sala.")
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_baja = models.DateField(null=True, blank=True, help_text="Fecha de egreso o abandono en esta sala particular.")
    motivo_baja = models.TextField(blank=True, help_text="Motivo por el que se dio de baja.")

    class Meta:
        unique_together = ("alumno", "sala")
        verbose_name = "Asignación a Sala"
        verbose_name_plural = "Asignaciones a Salas"

    def clean(self):
        if not self.activo and not self.fecha_baja:
            raise ValidationError({"fecha_baja": "Debe indicar la fecha de baja si la asignación no está activa."})
        if self.activo and self.fecha_baja:
            raise ValidationError({"fecha_baja": "Una asignación activa no puede tener fecha de baja."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alumno} en {self.sala.nombre}"


class MotivoJustificacion(models.Model):
    """
    Catálogo de razones por las cuales un alumno puede faltar,
    llegar tarde o retirarse antes (Salud, Cita Médica, Trámite, etc.).
    """
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Motivo de Justificación"
        verbose_name_plural = "Motivos de Justificación"

    def __str__(self):
        return self.nombre
    
class Asistencia(models.Model):
    """
    Registro diario de la presencia del alumno en su sala.
    Permite rastrear llegadas tarde y retiros tempranos además de faltas justificadas.
    """
    ESTADO_CHOICES = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('J', 'Justificado'),
        ('T', 'Llegada Tarde'),
        ('R', 'Retiro Temprano'),
    ]
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="asistencias")
    sala = models.ForeignKey("jardines.Sala", on_delete=models.CASCADE, related_name="asistencias", null=True, blank=True)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    docente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, help_text="Docente que registró la asistencia.")
    motivo = models.ForeignKey(
        MotivoJustificacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Motivo obligatorio si el estado es Justificado, opcional para Tarde o Retiro."
    )
    observaciones = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Texto libre para especificar justificación si se selecciona 'Otro' o aclaraciones extra."
    )

    class Meta:
        unique_together = ("alumno", "sala", "fecha")
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        
    def clean(self):
        """Valida que los motivos solo se asignen cuando el estado lo requiere o permite."""
        if self.estado == 'P' and self.motivo:
            raise ValidationError(
                "Un alumno presente no puede tener motivo de inasistencia."
            )

        if self.estado == 'J' and not self.motivo:
            raise ValidationError(
                "Una asistencia justificada requiere un motivo obligatorio."
            )

        if self.fecha > date.today():
            raise ValidationError(
                "No se puede registrar asistencia en fechas futuras."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} - {self.alumno}: {self.get_estado_display()}"

class Tutor(models.Model):
    """
    Representa a un padre, madre o encargado responsable del alumno.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^[\d\.-]+$',
            message='El DNI solo puede contener números, puntos o guiones.'
        )],
        unique=True
    )
    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"

class Inscripcion(models.Model):
    """
    Registro temporal de una solicitud de inscripción (Pre-inscripción).
    """
    programa = models.ForeignKey(
        "jardines.Programa",
        on_delete=models.PROTECT
    )
    subprograma = models.ForeignKey(
        "jardines.Subprograma",
        on_delete=models.PROTECT
    )
    espacio = models.ForeignKey(
        "jardines.Jardin",
        on_delete=models.PROTECT
    )
    sala = models.ForeignKey(
        "jardines.Sala",
        on_delete=models.PROTECT
    )

    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=50, blank=True)
    direccion = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        
    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.programa.nombre})"
    
class FichaProgramaAlumno(models.Model):
    """
    Extensión del legajo con datos socio-demográficos específicos.
    """
    alumno = models.OneToOneField(
        "Alumno",
        on_delete=models.CASCADE,
        related_name="ficha_programa"
    )

    sabe_leer = models.BooleanField(null=True, blank=True)
    sabe_escribir = models.BooleanField(null=True, blank=True)
    nivel_educativo = models.CharField(max_length=100, blank=True)
    situacion_laboral = models.CharField(max_length=100, blank=True)
    asistencia_social = models.BooleanField(null=True, blank=True)
    observaciones_programa = models.TextField(blank=True)
    
    telefono = models.CharField(max_length=20, blank=True)
    escolaridad = models.CharField(max_length=100, blank=True)
    obra_social = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ficha programa - {self.alumno}"


# Create your models here.
