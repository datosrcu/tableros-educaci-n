from django.test import RequestFactory
from users.models import Usuario
from alumnos.views import resumen_mensual_docente
req = RequestFactory().get('/alumnos/docente/resumen-mensual/?mes=7&anio=2026')
try:
    req.user = Usuario.objects.get(username='YAMILAGALLARDO')
    print("User found")
    resp = resumen_mensual_docente(req)
    print("Response status:", resp.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()
