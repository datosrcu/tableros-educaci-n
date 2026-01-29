from django.db import models
from jardines.models import Sala
from users.models import Usuario
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class Alumno(models.Model):
    dni_validator = RegexValidator(
    regex=r'^\d{2}\.\d{3}\.\d{3}$',
    message='El DNI debe tener el formato XX.XXX.XXX'
)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(
    max_length=10,
    unique=True,
    validators=[dni_validator]
)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, related_name="alumnos")
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    tutores = models.ManyToManyField('Tutor', related_name='alumnos', blank=True)

    def clean(self):
        if not self.sala:
            raise ValidationError("El alumno debe estar asignado a una sala.")

        if not self.nombre.strip():
            raise ValidationError("El nombre del alumno no puede estar vacío.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"
    
    def dni_formateado(self):
        dni = self.dni.replace(".", "")
        return f"{dni[:2]}.{dni[2:5]}.{dni[5:]}"
    
    dni_formateado.short_description = 'DNI'

class MotivoJustificacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('J', 'Justificado'),
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
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{2}\.\d{3}\.\d{3}$',
            message='El DNI debe tener el formato XX.XXX.XXX'
        )],
        unique=True
    )
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"


# Create your models here.
