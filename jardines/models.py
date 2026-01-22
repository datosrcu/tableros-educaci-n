from django.db import models
from django.conf import settings

class Programa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

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
    direccion = models.TextField(max_length=150)
    subprograma = models.CharField(max_length=100)
    coordenadas = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, choices=SECTORES_CHOICES)
    
    programa = models.ForeignKey(
    Programa,
    on_delete=models.PROTECT,
    related_name="jardines"
    )

    def __str__(self):
        return self.nombre

class Sala(models.Model):
    TURNO_CHOICES = [
        ("M", "Mañana"),
        ("T", "Tarde"),
        ("J", "Jornada Completa")
    ]
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE, related_name="salas")
    nombre = models.CharField(max_length=100)
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)
    horario_inicio = models.TimeField(max_length=5, default="08:00")
    horario_fin = models.TimeField(max_length=5, default="12:00")
    docentes = models.ManyToManyField('users.Usuario', related_name='salas', blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.get_turno_display()}"


