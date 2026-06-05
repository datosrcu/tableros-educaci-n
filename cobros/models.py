from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from jardines.models import Programa, Subprograma, Sala
from alumnos.models import Alumno

MESES_NOMBRES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

class ProgramaCobro(models.Model):
    """
    Configuración de programas que cobran cuota.
    """
    programa = models.OneToOneField(
        Programa,
        on_delete=models.CASCADE,
        related_name="configuracion_cobro",
        verbose_name="Programa"
    )
    importe_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importe Mensual"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Programa con Cobro"
        verbose_name_plural = "Programas con Cobro"

    def clean(self):
        if self.importe_mensual is not None and self.importe_mensual < 0:
            raise ValidationError({"importe_mensual": "El importe mensual no puede ser negativo."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.programa.nombre} - ${self.importe_mensual}"


class ResponsableCobro(models.Model):
    """
    Usuarios habilitados para gestionar cobros de un programa específico.
    """
    ROLES = (
        ("titular", "Titular"),
        ("suplente", "Suplente"),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="responsabilidades_cobro",
        verbose_name="Usuario"
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name="responsables_cobro",
        verbose_name="Programa"
    )
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default="titular",
        verbose_name="Rol"
    )

    class Meta:
        verbose_name = "Responsable de Cobro"
        verbose_name_plural = "Responsables de Cobro"
        unique_together = ("usuario", "programa")

    def clean(self):
        if self.usuario and self.usuario.rol not in ["coordinador", "administrador"] and not self.usuario.is_superuser:
            raise ValidationError({"usuario": "El usuario responsable de cobro debe tener rol 'coordinador' o 'administrador'."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.programa.nombre} ({self.get_rol_display()})"


class Pago(models.Model):
    """
    Registro de pagos realizados por los alumnos.
    """
    METODOS_PAGO = (
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
    )
    ESTADOS = (
        ("pagado", "Pagado"),
        ("adeuda", "Adeuda"),
    )

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Alumno"
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Programa"
    )
    subprograma = models.ForeignKey(
        Subprograma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos",
        verbose_name="Subprograma"
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos",
        verbose_name="Sala"
    )
    importe = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importe"
    )
    fecha_pago = models.DateField(
        verbose_name="Fecha de Pago"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        verbose_name="Método de Pago"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pagado",
        verbose_name="Estado"
    )
    mes_pagado = models.IntegerField(
        choices=[(i, MESES_NOMBRES[i]) for i in range(1, 13)],
        verbose_name="Mes Pagado",
        default=timezone.now().month
    )
    anio_pagado = models.IntegerField(
        verbose_name="Año Pagado",
        default=timezone.now().year
    )
    enviar_correo = models.BooleanField(
        default=False,
        verbose_name="Enviar por correo"
    )
    correo_envio = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo de envío"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos_registrados",
        verbose_name="Registrado Por"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago", "-created_at"]

    def clean(self):
        if self.importe is not None and self.importe < 0:
            raise ValidationError({"importe": "El importe del pago no puede ser negativo."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alumno} - {self.programa.nombre} - ${self.importe} ({self.get_estado_display()})"

    @property
    def numero_comprobante(self):
        """Genera un número único de comprobante."""
        return f"BC-{self.anio_pagado}-{self.id:06d}"
