import json
from jardines.models import Jardin
j_obj = Jardin.objects.filter(**{"programa__nombre": "Espacios lúdicos y de aprendizaje para la primera infancia"})
res = [j.nombre for j in j_obj if j.nombre in ('NUEVA ARGENTINA', 'GORRIONCITOS', 'MERCANTILITOS')]

print("MATCHED:", res)
