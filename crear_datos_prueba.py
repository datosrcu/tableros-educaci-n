import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from jardines.models import Programa, Subprograma, Jardin, Sala
from alumnos.models import Inscripcion
from formularios.models import EstructuraFormulario, CampoFormulario
from datetime import date

# 1. Crear Programa y Estructura
programa, _ = Programa.objects.get_or_create(nombre="Programa Demo Form", defaults={"activo": True})
estructura, created = EstructuraFormulario.objects.get_or_create(programa=programa)

if created:
    print(f"Estructura creada para {programa.nombre}")
    # Crear campos
    CampoFormulario.objects.create(estructura=estructura, etiqueta="¿Alergias?", nombre_interno="alergias", tipo="texto", orden=1)
    CampoFormulario.objects.create(estructura=estructura, etiqueta="Cantidad de hermanos", nombre_interno="cant_hermanos", tipo="numero", orden=2)
    CampoFormulario.objects.create(estructura=estructura, etiqueta="¿Sabe nadar?", nombre_interno="sabe_nadar", tipo="booleano", orden=3)
    CampoFormulario.objects.create(estructura=estructura, etiqueta="Deporte favorito", nombre_interno="deporte", tipo="select", opciones="Fútbol, Voley, Basket", orden=4)
else:
    print(f"Estructura ya existía para {programa.nombre}")

# 2. Crear Inscripción de prueba
subprograma, _ = Subprograma.objects.get_or_create(programa=programa, nombre="Sub Demo")
jardin, _ = Jardin.objects.get_or_create(programa=programa, subprograma=subprograma, nombre="Jardin Demo", defaults={"direccion": "Calle 123", "sector": "Norte"})
sala, _ = Sala.objects.get_or_create(jardin=jardin, nombre="Sala Demo", turno="mañana")

inscripcion, _ = Inscripcion.objects.get_or_create(
    dni="99999999",
    defaults={
        "programa": programa,
        "subprograma": subprograma,
        "espacio": jardin,
        "sala": sala,
        "apellido": "Test",
        "nombre": "Manual",
        "fecha_nacimiento": date(2018, 1, 1)
    }
)

print(f"Datos de prueba listos.")
print(f"URL para probar: /formularios/responder/{inscripcion.id}/")
