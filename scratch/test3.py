import json
from jardines.models import Jardin
j_obj = Jardin.objects.all().order_by('nombre')
res = [j.nombre for j in j_obj if j.nombre in ('NUEVA ARGENTINA', 'GORRIONCITOS', 'MERCANTILITOS')]

print(res)
