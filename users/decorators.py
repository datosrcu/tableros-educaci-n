from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def rol_requerido(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.rol == "administrador":
                return view_func(request, *args, **kwargs)

            if request.user.rol not in roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def solo_coordinador(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.rol in ["coordinador", "administrador"]:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

