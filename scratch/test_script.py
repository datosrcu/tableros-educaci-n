import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from jardines.models import Jardin

jardines_obj = Jardin.objects.all()
res = []
for j in jardines_obj:
  if j.coordenadas:
    try:
      coord_clean = j.coordenadas.replace("'", "").replace('"', '')
      lat, lon = map(float, coord_clean.split(','))
      res.append({
          "nombre": j.nombre,
          "lat": lat,
          "lon": lon,
          "subprograma": j.subprograma.nombre if j.subprograma else "Sin Subprograma"
      })
    except Exception as e:
      res.append({"nombre": j.nombre, "error": str(e)})

print(json.dumps([r for r in res if r['nombre'] in ('NUEVA ARGENTINA', 'GORRIONCITOS', 'MERCANTILITOS')], indent=2))
