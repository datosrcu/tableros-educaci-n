"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import views as auth_views, logout as django_logout
from users.views import crear_docente
from django.views.generic import RedirectView  # ← Importar correctamente

def logout_view(request):
    django_logout(request)
    return redirect("login")

from config.middleware import is_maintenance_mode_active

def mantenimiento_view(request):
    """Vista directa para el estado de mantenimiento programado."""
    return render(request, "mantenimiento.html", status=200)

def home_redirect(request):
    if is_maintenance_mode_active():
        return render(request, "mantenimiento.html", status=200)

    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.rol == "coordinador":
        return redirect("users:dashboard_coordinador")
    if request.user.rol in ("docente", "auxiliar"):
        return redirect("alumnos:dashboard_docente")

    return redirect("/admin/")

from django.http import HttpResponse

def health_check(request):
    """Endpoint para el healthcheck de Docker. No toca la DB."""
    return HttpResponse("OK", status=200, content_type="text/plain")

from jardines import views as jardines_views

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('mantenimiento/', mantenimiento_view, name='mantenimiento'),
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
    
    # Rutas públicas directas de Tableros (/tableros/...)
    path("tableros/espacios-ludicos/", jardines_views.DashboardEspaciosLudicosView.as_view(), name="tablero_espacios_ludicos"),
    path("tableros/alfabetizacion/", jardines_views.DashboardAlfabetizacionView.as_view(), name="tablero_alfabetizacion"),
    path("tableros/carpinteria/", jardines_views.DashboardCarpinteriaView.as_view(), name="tablero_carpinteria"),
    path("tableros/artes-plasticas/", jardines_views.DashboardArtesPlasticasView.as_view(), name="tablero_artes_plasticas"),
    path("tableros/expresion-cultural/", jardines_views.DashboardExpresionCulturalView.as_view(), name="tablero_expresion_cultural"),
    path("tableros/", RedirectView.as_view(url='/tableros/espacios-ludicos/'), name="tableros_index"),

    path(
        'imprimir-asistencias-sala/<int:sala_id>/',
        RedirectView.as_view(url=reverse_lazy('alumnos:imprimir_asistencias_sala_docente', args=[0])),
        name='imprimir_asistencias_sala',
    ),
]