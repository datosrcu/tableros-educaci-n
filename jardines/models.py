from django.db import models
from users.models import Usuario

class Jardin(models.Model):
    SUBPROGRAMA_CHOICES = [
        ('Centros Educativos Infantiles Municipales', 'centros educativos infantiles municipales'),
        ('Salas Cuna', 'salas cuna'),
    ]
    SECTORES_CHOICES =   [
        ('Norte', 'norte'),
        ('Sur', 'sur'),
        ('Este', 'este'),
        ('Oeste', 'oeste'),
        ('Centro', 'centro'),
    ] 
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    subprograma = models.CharField(choices=SUBPROGRAMA_CHOICES)
    coordenadas = models.CharField(max_length=100, blank=True)
    sector = models.CharField(choices=SECTORES_CHOICES)

    def __str__(self):
        return self.nombre

class Sala(models.Model):
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
    ]
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    turno = models.CharField(choices=TURNO_CHOICES)
    horario_inicio = models.TimeField(default="08:00")
    horario_fin = models.TimeField(default="12:00")
    docentes = models.ManyToManyField(Usuario, related_name='salas_asignadas')
    
    def __str__(self):
        return f"{self.nombre} ({self.jardin.nombre})"

# Create your models here.
