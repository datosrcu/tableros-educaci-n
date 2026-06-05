"""
Modelos de usuario y auditoría.
Implementa un modelo de usuario personalizado con roles y un sistema de logs.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Usuario(AbstractUser):
    """
    Modelo de usuario extendido con roles específicos para el Sistema Jardines.
    Roles disponibles: administrador, coordinador, docente.
    """
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

    # 🆔 Datos personales complementarios
    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DNI / Pasaporte"
    )
    telefono = models.CharField(max_length=50, blank=True)
    
    # 🏫 Relaciones
    programas_asignados = models.ManyToManyField(
        "jardines.Programa",
        blank=True,
        related_name="coordinadores",
        help_text="Programas sobre los cuales un Coordinador tiene gestión."
    )

    # =====================================================
    # MÉTODOS DE CONSULTA (Helpers de permisos)
    # =====================================================

    def es_admin(self):
        """Verifica si el usuario tiene privilegios administrativos."""
        return self.rol == "administrador" or self.is_superuser

    def es_coordinador(self):
        """Verifica si el usuario es coordinador."""
        return self.rol == "coordinador"

    def es_docente(self):
        """Verifica si el usuario es docente."""
        return self.rol == "docente"

    @property
    def puede_gestionar_cobros(self):
        """Verifica si el usuario tiene permiso para gestionar cobros."""
        if self.is_superuser or self.rol == "administrador":
            return True
        from cobros.models import ResponsableCobro
        return ResponsableCobro.objects.filter(usuario=self).exists()

    # =====================================================
    # VALIDACIONES DE NEGOCIO
    # =====================================================

    def clean(self):
        """
        Garantiza la separación de responsabilidades:
        Admin/Coordinador no deben estar asignados a salas directamente (soft-check).
        """
        super().clean()

        # 🔒 Coordinador no puede tener salas asignadas (regla de negocio v1)
        if self.rol == "coordinador" and self.pk:
            if self.salas_asignadas.exists():
                raise ValidationError(
                    "Un coordinador no puede tener salas asignadas directamente."
                )

        # 🔒 Administrador no puede tener salas asignadas
        if self.rol == "administrador" and self.pk:
            if self.salas_asignadas.exists():
                raise ValidationError(
                    "Un administrador no puede tener salas asignadas directamente."
                )

    # =====================================================
    # SINCRONIZACIÓN DE PERMISOS DJANGO
    # =====================================================

    def save(self, *args, **kwargs):
        """
        Sincroniza flags de Django (is_staff) basado en el rol de negocio.
        """
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
    """
    Log de auditoría para rastrear acciones críticas en el sistema.
    Almacena quién hizo qué, en qué modelo y cuándo.
    """
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
