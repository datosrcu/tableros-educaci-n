"""
Middleware para el control de modo mantenimiento en el Sistema Presente GRCU.
Permite mostrar una página institucional de mantenimiento sin tocar la base de datos MySQL.
"""
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

_BYPASS_PATHS = ('/health/', '/static/', '/media/', '/favicon.ico')

class MaintenanceModeMiddleware:
    """
    Si MAINTENANCE_MODE está activo, intercepta todas las solicitudes
    (excepto health checks y estáticos) y sirve la plantilla de mantenimiento
    sin ejecutar consultas a la base de datos.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Permitir bypass para rutas de sistema y archivos estáticos
        if any(path.startswith(bp) for bp in _BYPASS_PATHS):
            return self.get_response(request)

        # Bypass opcional para pruebas de administración mediante parámetro seguro
        if request.GET.get('bypass_mantenimiento') == 'grcu_admin_2026':
            return self.get_response(request)

        # Si el modo mantenimiento está habilitado en settings
        if getattr(settings, 'MAINTENANCE_MODE', False):
            # Servir directamente la página de mantenimiento con status 503
            # (o 200 en la raíz para navegadores de usuario)
            status_code = 200 if path == '/' or path == '/mantenimiento/' else 503
            response = render(request, "mantenimiento.html", status=status_code)
            response['Retry-After'] = '7200'  # 2 horas (10hs a 12hs)
            return response

        return self.get_response(request)
