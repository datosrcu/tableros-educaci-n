import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from jardines.models import Jardin

jardines_obj = Jardin.objects.filter(programa__nombre="Espacios lúdicos y de aprendizaje para la primera infancia")
for j in jardines_obj:
    if j.nombre in ['GORRIONCITOS', 'NUEVA ARGENTINA']:
        print("NAME:", j.nombre)
        print("COORDENADAS:", repr(j.coordenadas))
        if j.coordenadas:
            try:
                coord_clean = j.coordenadas.replace("'", "").replace('"', '')
                lat, lon = map(float, coord_clean.split(','))
                print("LAT LON PARSED:", lat, lon)
            except Exception as e:
                print("ERROR PARSING:", e)
        print("-" * 20)
