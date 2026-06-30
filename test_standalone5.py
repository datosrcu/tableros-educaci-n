import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from jardines.models import Jardin

for j in Jardin.objects.all():
    if j.coordenadas and ('33.11865' in j.coordenadas or '33.1386' in j.coordenadas):
        print(j.nombre, j.coordenadas)
