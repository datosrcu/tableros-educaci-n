from django.db import models
from jardines.models import Programa
from alumnos.models import Inscripcion


class EstructuraFormulario(models.Model):
    programa = models.OneToOneField(
        Programa,
        on_delete=models.CASCADE,
        related_name="estructura_formulario"
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Estructura - {self.programa.nombre}"


class CampoFormulario(models.Model):

    TIPOS = (
        ("texto", "Texto corto"),
        ("textarea", "Texto largo"),
        ("numero", "Número"),
        ("fecha", "Fecha"),
        ("booleano", "Sí / No"),
        ("select", "Lista desplegable"),
    )

    estructura = models.ForeignKey(
        EstructuraFormulario,
        on_delete=models.CASCADE,
        related_name="campos"
    )

    etiqueta = models.CharField(max_length=200)
    nombre_interno = models.SlugField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    obligatorio = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    opciones = models.TextField(blank=True)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return f"{self.etiqueta} ({self.tipo})"





class RespuestaFormulario(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="respuestas_formulario",
        null=True,
        blank=True
    )
    alumno = models.ForeignKey(
        "alumnos.Alumno",
        on_delete=models.CASCADE,
        related_name="respuestas_formulario",
        null=True,
        blank=True
    )
    formulario = models.ForeignKey(
        EstructuraFormulario,
        on_delete=models.PROTECT
    )
    datos = models.JSONField(default=dict)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta de {self.inscripcion} - {self.fecha_creacion}"

