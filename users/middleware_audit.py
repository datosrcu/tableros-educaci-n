import threading

_thread_locals = threading.local()

# Rutas que nunca deben tocar la base de datos
_BYPASS_PATHS = ('/health/', '/favicon.ico', '/static/', '/media/')

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = None
        try:
            # Bypass total para healthchecks y archivos estáticos
            path = request.path_info
            if any(path.startswith(bp) for bp in _BYPASS_PATHS):
                return self.get_response(request)

            if hasattr(request, "user"):
                user = request.user
                # Usar getattr para no forzar evaluación del LazyObject si no está autenticado
                if getattr(user, "is_authenticated", False):
                    _thread_locals.user = user

            response = self.get_response(request)
        finally:
            _thread_locals.user = None
        return response
