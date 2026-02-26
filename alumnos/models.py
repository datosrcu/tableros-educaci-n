from django.db import models
from jardines.models import Sala
from users.models import Usuario
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sala = models.ForeignKey("jardines.Sala", on_delete=models.PROTECT)
    tutores = models.ManyToManyField("Tutor", related_name="alumnos", blank=True)
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateField(null=True, blank=True)

    def clean(self):
        # 🔹 DNI solo números
        if not self.dni.isdigit():
            raise ValidationError({"dni": "El DNI debe contener solo números."})

        # 🔹 Edad razonable (ejemplo: 0.5 a 18 años para incluir maternales)
        dias_vividos = (date.today() - self.fecha_nacimiento).days
        edad_anios = dias_vividos / 365.25
        if edad_anios < 0.5 or edad_anios > 18:
            raise ValidationError({
                "fecha_nacimiento": "La edad del alumno no es válida para este sistema (debe tener entre 6 meses y 18 años)."
            })

        # 🔹 Si no está activo → debe tener fecha_baja
        if not self.activo and not self.fecha_baja:
            raise ValidationError({
                "fecha_baja": "Debe indicar la fecha de baja."
            })

        # 🔹 Si está activo → no puede tener fecha_baja
        if self.activo and self.fecha_baja:
            raise ValidationError({
                "fecha_baja": "Un alumno activo no puede tener fecha de baja."
            })

    def save(self, *args, **kwargs):
        self.full_clean()  # 🔥 fuerza validaciones siempre
        super().save(*args, **kwargs)


class MotivoJustificacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('J', 'Justificado'),
        ('T', 'Llegada Tarde'),
        ('R', 'Retiro Temprano'),
    ]
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    docente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    motivo = models.ForeignKey(
    MotivoJustificacion,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
    
)
    class Meta:
        unique_together = ("alumno", "fecha")
        
    def clean(self):
        if self.estado == 'P' and self.motivo:
            raise ValidationError(
                "Un alumno presente no puede tener motivo."
            )

        if self.estado == 'J' and not self.motivo:
            raise ValidationError(
                "Una asistencia justificada requiere un motivo."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.fecha} - {self.alumno.apellido}, {self.alumno.nombre}: {self.estado}"

class Tutor(models.Model):
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
    email = models.EmailField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"

class Inscripcion(models.Model):
    # Relaciones
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

    # Datos personales (comunes a TODOS)
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
        
    def clean(self):
        pass

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.programa})"
    
class FichaProgramaAlumno(models.Model):
    alumno = models.OneToOneField(
        "Alumno",
        on_delete=models.CASCADE,
        related_name="ficha_programa"
    )

    # Campos genéricos reutilizables
    sabe_leer = models.BooleanField(null=True, blank=True)
    sabe_escribir = models.BooleanField(null=True, blank=True)

    nivel_educativo = models.CharField(
        max_length=100,
        blank=True
    )

    situacion_laboral = models.CharField(
        max_length=100,
        blank=True
    )

    asistencia_social = models.BooleanField(null=True, blank=True)

    observaciones_programa = models.TextField(blank=True)
    
    telefono = models.CharField(max_length=20, blank=True)
    escolaridad = models.CharField(max_length=100, blank=True)
    obra_social = models.CharField(max_length=100, blank=True)

    def clean(self):
        pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ficha programa - {self.alumno}"


# Create your models here.
