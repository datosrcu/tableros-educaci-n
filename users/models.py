from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from jardines.models import Sala
dni_validator = RegexValidator(
    regex=r'^\d{2}\.\d{3}\.\d{3}$',
    message='El DNI debe tener el formato XX.XXX.XXX'
)

class Usuario(AbstractUser):
    ROLES = (
    ("admin", "Administrador"),
    ("docente", "Docente"),
    )

    rol = models.CharField(max_length=20, choices=ROLES, default="docente")
    
    dni = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        validators=[dni_validator]
    )
    es_docente = models.BooleanField(default=False)
    salas = models.ManyToManyField(Sala, blank=True, related_name="docentes_asignados")

    def __str__(self):
        return self.get_full_name() or self.username

# Create your models here.
