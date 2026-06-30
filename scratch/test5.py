import json
from jardines.models import Jardin
j_obj = Jardin.objects.all()
res = [repr(j.programa.nombre) for j in j_obj if j.nombre == 'GORRIONCITOS']

print("PROGRAMA GORRIONCITOS:", res)
