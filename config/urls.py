"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views, logout as django_logout
from users.views import crear_docente

def logout_view(request):
    django_logout(request)
    return redirect("login")

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.rol == "coordinador":
        return redirect("users:dashboard_coordinador")
    if request.user.rol == "docente":
        return redirect("alumnos:dashboard_docente")

    return redirect("/admin/")


from django.http import HttpResponse

def health_check(request):
    """Endpoint para el healthcheck de Docker. No toca la DB."""
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),

    path('', home_redirect),
    path('admin-panel/', admin.site.urls),
    path('admin/', lambda r: redirect('/admin-panel/')),
    path('login/', lambda r: redirect('login')),
    path('logout/', logout_view, name='logout_alias'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('', include('alumnos.urls')),
    path('registro/docente/', crear_docente, name='registrar_docente'),
    path("jardines/", include("jardines.urls")),
    path("usuarios/", include("users.urls")),
    path("formularios/", include("formularios.urls")),
    path("cobros/", include("cobros.urls")),
]
