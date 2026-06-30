import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from jardines.models import Programa
for p in Programa.objects.all():
    print(repr(p.nombre))
