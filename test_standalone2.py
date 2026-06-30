import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from jardines.models import Programa
for p in Programa.objects.all():
    if "Espacios l" in p.nombre:
        p.nombre = 'Espacios l\u00fadicos y de aprendizaje para la primera infancia'
        p.save()
        print("Fixed!", repr(p.nombre))
