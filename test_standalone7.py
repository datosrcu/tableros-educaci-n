import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.test import RequestFactory
from jardines.views import DashboardEspaciosLudicosView

factory = RequestFactory()
request = factory.get('/dashboard/', {'fecha': '2026-05'})
view = DashboardEspaciosLudicosView.as_view()
response = view(request)
context = response.context_data
print("MES LABEL IN CONTEXT:", context.get("mes_nombre_reporte"))
