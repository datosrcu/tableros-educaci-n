from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Usuario(AbstractUser):

    ROLES = (
        ("administrador", "Administrador"),
        ("coordinador", "Coordinador"),
        ("docente", "Docente"),
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default="docente",
    )

    # 🆔 Datos personales
    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DNI / Pasaporte"
    )
    telefono = models.CharField(max_length=50, blank=True)

    # =====================================================
    # MÉTODOS DE CONSULTA
    # =====================================================

    def es_admin(self):
        return self.rol == "administrador" or self.is_superuser

    def es_coordinador(self):
        return self.rol == "coordinador"

    def es_docente(self):
        return self.rol == "docente"

    # =====================================================
    # VALIDACIONES
    # =====================================================

    def clean(self):
        super().clean()

        # 🔒 Coordinador no puede tener salas asignadas
        if self.rol == "coordinador" and self.pk:
            if self.salas_asignadas.exists():
                raise ValidationError(
                    "Un coordinador no puede tener salas asignadas."
                )

        # 🔒 Administrador no puede tener salas asignadas
        if self.rol == "administrador" and self.pk:
            if self.salas_asignadas.exists():
                raise ValidationError(
                    "Un administrador no puede tener salas asignadas."
                )

    # =====================================================
    # SINCRONIZACIÓN DE PERMISOS
    # =====================================================

    def save(self, *args, **kwargs):

        # 🔐 Sincronizar permisos con rol
        if self.rol == "administrador":
            self.is_staff = True

        elif self.rol == "coordinador":
            self.is_staff = False
            self.is_superuser = False

        elif self.rol == "docente":
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)


# Create your models here.
