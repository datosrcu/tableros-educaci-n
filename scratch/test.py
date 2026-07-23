import json
from jardines.models import Jardin

j_list = Jardin.objects.filter(nombre__in=['NUEVA ARGENTINA', 'GORRIONCITOS', 'MERCANTILITOS'])
res = []
for j in j_list:
  res.append((j.nombre, j.programa.nombre if j.programa else "NONE", j.subprograma.nombre if j.subprograma else "NONE"))
print("PROGRAMAS:", json.dumps(res))
