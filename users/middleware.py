from django.shortcuts import redirect

_BYPASS_PATHS = ('/health/', '/static/', '/media/', '/favicon.ico')

class BloquearAdminADocentesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Nunca tocar auth en rutas de sistema
        if any(path.startswith(bp) for bp in _BYPASS_PATHS):
            return self.get_response(request)

        if path.startswith("/admin"):
            user = request.user
            if user.is_authenticated:
                if getattr(user, "rol", None) == "docente":
                    return redirect("alumnos:dashboard_docente")
            # si no está logueado, Django maneja el login

        return self.get_response(request)
