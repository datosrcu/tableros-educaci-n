from django.shortcuts import redirect
from django.urls import reverse

class BloquearAdminADocentesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            user = request.user

            if user.is_authenticated:
                if getattr(user, "rol", None) == "docente":
                    return redirect("alumnos:dashboard")
            else:
                # si no está logueado, dejamos que Django maneje el login
                pass

        return self.get_response(request)
