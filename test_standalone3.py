import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from jardines.models import Jardin

jardines = Jardin.objects.filter(programa__nombre="Espacios lúdicos y de aprendizaje para la primera infancia")
print("Total jardines matching:", jardines.count())
