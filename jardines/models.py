from django.db import models
from django.conf import settings

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
    direccion = models.TextField(max_length=100)
    subprograma = models.CharField(max_length=100, choices=SUBPROGRAMA_CHOICES)
    coordenadas = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, choices=SECTORES_CHOICES)

    def __str__(self):
        return self.nombre

class Sala(models.Model):
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
    ]
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)
    horario_inicio = models.TimeField(max_length=5, default="08:00")
    horario_fin = models.TimeField(max_length=5, default="12:00")
    docentes = models.ManyToManyField('users.Usuario', related_name='salas_asignadas')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.jardin.nombre})"

