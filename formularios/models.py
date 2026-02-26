"""
Modelos para el motor de formularios dinámicos.
Permite definir estructuras de campos personalizadas por programa y recolectar datos de alumnos.
"""
from django.db import models
from jardines.models import Programa
from alumnos.models import Inscripcion


class EstructuraFormulario(models.Model):
    """
    Contenedor de campos personalizados para un Programa específico.
    Actúa como cabecera del formulario dinámico.
    """
    programa = models.OneToOneField(
        Programa,
        on_delete=models.CASCADE,
        related_name="estructura_formulario",
        help_text="Programa al que pertenece esta configuración de campos."
    )

    activo = models.BooleanField(
        default=True,
        help_text="Define si el formulario debe mostrarse en la carga de alumnos."
    )

    def __str__(self):
        return f"Estructura - {self.programa.nombre}"


class CampoFormulario(models.Model):
    """
    Definición individual de un campo (pregunta) dentro de una Estructura.
    Controla el tipo de dato, validación y orden de visualización.
    """
    TIPOS = (
        ("texto", "Texto corto"),
        ("textarea", "Texto largo"),
        ("numero", "Número"),
        ("fecha", "Fecha"),
        ("booleano", "Sí / No (Checkbox)"),
        ("select", "Lista desplegable"),
    )

    estructura = models.ForeignKey(
        EstructuraFormulario,
        on_delete=models.CASCADE,
        related_name="campos"
    )

    etiqueta = models.CharField(max_length=200, help_text="Nombre visible para el usuario.")
    nombre_interno = models.SlugField(help_text="Identificador único del campo (sin espacios ni caracteres especiales).")
    tipo = models.CharField(max_length=20, choices=TIPOS)
    obligatorio = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Posición relativa del campo en el formulario."
    )
    opciones = models.TextField(
        blank=True,
        help_text="Solo para 'select': valores separados por coma (ej: Opción 1, Opción 2)."
    )

    class Meta:
        ordering = ["orden"]
        verbose_name = "Campo de Formulario"
        verbose_name_plural = "Campos de Formulario"

    def __str__(self):
        return f"{self.etiqueta} ({self.tipo})"


class RespuestaFormulario(models.Model):
    """
    Almacena los valores recolectados de los campos dinámicos.
    Los datos se guardan en un campo JSON para mayor flexibilidad.
    """
    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="respuestas_formulario",
        null=True,
        blank=True,
        help_text="Vinculación opcional con una ficha de pre-inscripción."
    )
    alumno = models.ForeignKey(
        "alumnos.Alumno",
        on_delete=models.CASCADE,
        related_name="respuestas_formulario",
        null=True,
        blank=True,
        help_text="Vinculación con el legajo definitivo del alumno."
    )
    formulario = models.ForeignKey(
        EstructuraFormulario,
        on_delete=models.PROTECT
    )
    datos = models.JSONField(
        default=dict,
        help_text="Diccionario con pares {'nombre_interno': valor}."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Respuesta de Formulario"
        verbose_name_plural = "Respuestas de Formulario"

    def __str__(self):
        return f"Respuesta de {self.alumno or self.inscripcion} - {self.fecha_creacion}"

