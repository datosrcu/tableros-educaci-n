from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jardines.models import Sala

dni_validator = RegexValidator(
    regex=r'^\d{2}\.\d{3}\.\d{3}$',
    message='El DNI debe tener el formato XX.XXX.XXX'
)

class Usuario(AbstractUser):

    ROLES = (
        ("admin", "Administrador"),
        ("directivo", "Directivo"),
        ("docente", "Docente"),
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default="docente",
    )

    def es_admin(self):
        return self.rol == "admin" or self.is_superuser

    def es_directivo(self):
        return self.rol == "directivo"

    def es_docente(self):
        return self.rol == "docente"


# Create your models here.
