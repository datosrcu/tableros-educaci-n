"""
Middleware para el control de modo mantenimiento en el Sistema Presente GRCU.
Permite mostrar una página institucional de mantenimiento sin tocar la base de datos MySQL.
"""
import os
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

_BYPASS_PATHS = ('/health', '/healthz', '/ping', '/static/', '/media/', '/favicon.ico')

def is_maintenance_mode_active():
    """
    Determina si el modo mantenimiento está activo de forma dinámica y ultra-robusta.
    Prioridad:
    1. Si estamos en modo TESTING de Django, respeta el override de settings.
    2. Variable de entorno en tiempo de ejecución (MAINTENANCE_MODE o MODO_MANTENIMIENTO en Dokploy / Docker).
    3. Archivo flag en disco (./maintenance.flag o /tmp/maintenance.flag).
    4. Configuración en settings.py.
    """
    # En testing unitario respetamos el setting modificado por @override_settings
    if getattr(settings, 'TESTING', False):
        return getattr(settings, 'MAINTENANCE_MODE', False)

    # 1. Comprobación directa en os.environ (valores inyectados por Dokploy)
    for env_key in ('MAINTENANCE_MODE', 'MODO_MANTENIMIENTO'):
        raw_val = os.environ.get(env_key)
        if raw_val is not None:
            cleaned = str(raw_val).strip().strip('\'"').lower()
            if cleaned in ('1', 'true', 't', 'yes', 'y', 'on', 'si', 's', 'activo', 'habilitado'):
                return True
            if cleaned in ('0', 'false', 'f', 'no', 'n', 'off', 'inactivo', 'deshabilitado', ''):
                return False

    # 2. Comprobación de archivo flag en disco
    base_dir = getattr(settings, 'BASE_DIR', Path('.'))
    flag_candidates = (
        Path(base_dir) / 'maintenance.flag',
        Path(base_dir) / '.maintenance',
        Path('/tmp/maintenance.flag'),
        Path('/tmp/mantenimiento.flag'),
    )
    for flag_path in flag_candidates:
        try:
            if flag_path.exists():
                content = flag_path.read_text().strip().strip('\'"').lower()
                if content in ('0', 'false', 'f', 'no', 'off', 'inactivo'):
                    return False
                return True
        except Exception:
            pass

    # 3. Fallback a settings
    return getattr(settings, 'MAINTENANCE_MODE', False)

class MaintenanceModeMiddleware:
    """
    Si el modo mantenimiento está activo, intercepta todas las solicitudes
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

        # Si el modo mantenimiento está habilitado
        if is_maintenance_mode_active():
            # Servir directamente la página de mantenimiento
            status_code = 200 if path in ('/', '/mantenimiento/', '/mantenimiento') else 503
            response = render(request, "mantenimiento.html", status=status_code)
            response['Retry-After'] = '7200'  # 2 horas
            return response

        return self.get_response(request)
