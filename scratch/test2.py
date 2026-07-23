import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from jardines.models import Jardin
jardines_obj = Jardin.objects.all().order_by('nombre')
res = []
for j in jardines_obj:
  if j.coordenadas:
    try:
      coord_clean = j.coordenadas.replace("'", "").replace('"', '')
      lat, lon = map(float, coord_clean.split(','))
      res.append({'nombre': j.nombre, 'lat': lat, 'lon': lon})
    except Exception as e:
      print("ERROR parsing:", j.nombre, j.coordenadas, e)
print("SUCCESS:")
print(json.dumps([r for r in res if r['nombre'] in ('NUEVA ARGENTINA', 'GORRIONCITOS', 'MERCANTILITOS')], indent=2))
