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


class AccionAuditoria(models.Model):
    ACCIONES = (
        ("creacion", "Creación"),
        ("modificacion", "Modificación"),
        ("eliminacion", "Eliminación"),
        ("asignacion", "Asignación"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name="acciones_realizadas",
        verbose_name="Usuario responsable"
    )
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modelo = models.CharField(max_length=100)  # Nombre del modelo afectado
    objeto_id = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Acción de Auditoría"
        verbose_name_plural = "Log de Auditoría"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.modelo} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
