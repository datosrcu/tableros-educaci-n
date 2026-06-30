import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from jardines.models import Jardin

jardines = Jardin.objects.filter(programa__nombre="Espacios lúdicos y de aprendizaje para la primera infancia", subprograma__nombre="C.E.P.I")
print("Total CEPI jardines matching:", jardines.count())
for j in jardines:
    print(j.nombre, j.subprograma.nombre if j.subprograma else "None")
