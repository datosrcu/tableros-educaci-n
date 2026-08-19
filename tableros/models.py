from django.db import models
from django.contrib.auth.models import AbstractUser

class Programa(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Subprograma(models.Model):
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name="subprogramas")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.programa.nombre} - {self.nombre}"

class Jardin(models.Model):
    SECTORES_CHOICES = [
        ("Norte", "Zona Norte"),
        ("Sur", "Zona Sur"),
        ("Este", "Zona Este"),
        ("Oeste", "Zona Oeste"),
        ("Centro", "Zona Centro"),
        ("Banda Norte", "Banda Norte"),
        ("Alberdi", "Alberdi"),
    ]

    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)
    sector = models.CharField(max_length=50, choices=SECTORES_CHOICES, default="Centro")
    programa = models.ForeignKey(Programa, on_delete=models.SET_NULL, null=True, blank=True, related_name="jardines")
    subprograma = models.ForeignKey(Subprograma, on_delete=models.SET_NULL, null=True, blank=True, related_name="jardines")

    def __str__(self):
        return self.nombre

class Turno(models.Model):
    nombre = models.CharField(max_length=50) # Mañana, Tarde, Noche

    def __str__(self):
        return self.nombre

class Sala(models.Model):
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE, related_name="salas")
    nombre = models.CharField(max_length=100)
    turno = models.ForeignKey(Turno, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.jardin.nombre} - {self.nombre}"

class Usuario(models.Model):
    ROLES = [
        ("coordinador", "Coordinador"),
        ("docente", "Docente"),
        ("auxiliar", "Auxiliar"),
    ]

    nombre = models.CharField(max_length=150)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    rol = models.CharField(max_length=30, choices=ROLES, default="docente")
    salas_asignadas = models.ManyToManyField(Sala, blank=True, related_name="docentes")

    def __str__(self):
        return f"{self.nombre} ({self.rol})"

class Alumno(models.Model):
    nombre = models.CharField(max_length=150)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nombre

class AsignacionSala(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="asignaciones")
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="alumnos_asignados")
    fecha_ingreso = models.DateField()
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.alumno} -> {self.sala}"

class Asistencia(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="asistencias")
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()
    presente = models.BooleanField(default=True)
    motivo_ausencia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.alumno} - {self.fecha}: {'Presente' if self.presente else 'Ausente'}"
