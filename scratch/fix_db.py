import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix():
    from jardines.models import Programa
    for p in Programa.objects.all():
        print("Checking:", repr(p.nombre))
        if "ldicos" in p.nombre or "l\xfadicos" in p.nombre or p.nombre.startswith("Espacios l"):
            print("FOUND! Updating...")
            p.nombre = "Espacios lúdicos y de aprendizaje para la primera infancia"
            p.save()
            print("UPDATED.")

fix()
