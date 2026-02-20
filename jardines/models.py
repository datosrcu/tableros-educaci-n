from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower

class Programa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    usa_formulario_ampliado = models.BooleanField(
        default=False,
        help_text="Marca si este programa requiere el formulario ampliado de inscripción"
    )
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"

    def __str__(self):
        return self.nombre

class Subprograma(models.Model):
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='subprogramas'
    )
    nombre = models.CharField(max_length=100)
    
    usa_formulario_ampliado = models.BooleanField(
        default=False,
        help_text="Marca si este subprograma requiere formulario ampliado"
    )
    class Meta:
        verbose_name = "Subprograma"
        verbose_name_plural = "Subprogramas"
        unique_together = ("programa", "nombre")

    def __str__(self):
        return f"{self.programa} - {self.nombre}"


class Jardin(models.Model):
    programa = models.ForeignKey(
    Programa,
    on_delete=models.PROTECT,
    related_name="jardines",
    null=True,
    blank=True
    )
    
    subprograma = models.ForeignKey(
    Subprograma,
    on_delete=models.PROTECT,
    null=True,
    blank=True
    )
    
    SECTORES_CHOICES =   [
        ('Norte', 'norte'),
        ('Sur', 'sur'),
        ('Este', 'este'),
        ('Oeste', 'oeste'),
        ('Centro', 'centro'),
    ] 
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(max_length=150)
    coordenadas = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, choices=SECTORES_CHOICES)
    telefono = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Espacio"
        verbose_name_plural = "Espacios"
    
    
    def clean(self):
        if not self.programa:
            raise ValidationError("el jardín debe pertenecer a algún programa")
        
        if self.subprograma and self.subprograma.programa != self.programa:
            raise ValidationError("El subprograma no pertenece al programa seleccionado.")
        if not self.direccion.strip():
            raise ValidationError("La dirección no puede estar vacía.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)    

    def __str__(self):
        return self.nombre

class Sala(models.Model):

    jardin = models.ForeignKey(
        Jardin,
        on_delete=models.PROTECT,  # 🔒 más seguro
        related_name="salas"
    )

    nombre = models.CharField(max_length=100)

    turno = models.CharField(
        max_length=20,
        choices=(
            ("mañana", "Mañana"),
            ("tarde", "Tarde"),
        )
    )

    horario_inicio = models.TimeField(default="08:00")
    horario_fin = models.TimeField(default="12:00")

    docentes = models.ManyToManyField(
        "users.Usuario",
        related_name="salas_asignadas",
        blank=True,
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salas_responsables",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                "jardin",
                "turno",
                name="unique_sala_por_jardin_turno",
            )
        ]

    def clean(self):
        super().clean()

        errors = {}

        if not self.jardin:
            errors["jardin"] = "La sala debe pertenecer a un jardín."

        if self.horario_inicio and self.horario_fin:
            if self.horario_fin <= self.horario_inicio:
                errors["horario_fin"] = (
                    "El horario de fin debe ser posterior al inicio."
                )

        if self.responsable:
            if self.responsable.rol not in ["docente", "coordinador"]:
                errors["responsable"] = (
                    "El responsable debe ser docente o coordinador."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.turno}) - {self.jardin}"
 


