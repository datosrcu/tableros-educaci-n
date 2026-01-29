from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Programa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Subprograma(models.Model):
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='subprogramas'
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('programa', 'nombre')

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
    jardin = models.ForeignKey(Jardin, on_delete=models.CASCADE, related_name="salas")
    nombre = models.CharField(max_length=100)
    turno = models.CharField(
        max_length=20,
        choices=(
            ("mañana", "Mañana"),
            ("tarde", "Tarde"),
        )
    )
    horario_inicio = models.TimeField(max_length=5, default="08:00")
    horario_fin = models.TimeField(max_length=5, default="12:00")
    docentes = models.ManyToManyField("users.Usuario", related_name='salas_asignadas', limit_choices_to={"rol": "docente"}, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    related_name ="salas"
    
    def clean(self):
        errors = {}

        # 1️⃣ Jardín obligatorio
        if not self.jardin:
            errors["jardin"] = "La sala debe pertenecer a un jardín."

        # 2️⃣ Turno obligatorio
        if not self.turno:
            errors["turno"] = "Debe seleccionar un turno."

        # 3️⃣ Validación de unicidad lógica
        if self.jardin and self.turno and self.nombre:
            qs = Sala.objects.filter(
                jardin=self.jardin,
                turno=self.turno,
                nombre__iexact=self.nombre,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                errors["nombre"] = (
                    "Ya existe una sala con este nombre, turno y jardín."
                )
            if self.pk:
                for docente in self.docentes.all():
                    if docente.rol != "docente":
                        errors["docentes"] = "Solo usuarios con rol docente pueden asignarse."
    

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.turno}) - {self.jardin}"

 


