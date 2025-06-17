from django.db import models
from jardines.models import Sala
from users.models import Usuario
from django.core.validators import RegexValidator

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
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateField(null=True, blank=True)
    tutores = models.ManyToManyField('Tutor', related_name='alumnos')


    def __str__(self):
        return f"{self.apellido, self.nombre}"
    
    def dni_formateado(self):
        dni = self.dni.replace(".", "")
        return f"{dni[:2]}.{dni[2:5]}.{dni[5:]}"
    
    dni_formateado.short_description = 'DNI'

class MotivoJustificacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
class Asistencia(models.Model):
    ESTADOS = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('justificado', 'Justificado'),
    ]
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS)
    docente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    motivo = models.ForeignKey(
    MotivoJustificacion,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)

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
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"


# Create your models here.
