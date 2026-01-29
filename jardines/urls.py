from django.urls import path
from . import views

urlpatterns = [
    path("ajax/subprogramas/", views.cargar_subprogramas),
    path("ajax/jardines/", views.cargar_jardines),
    path("ajax/validar-docente-turno/", views.validar_docente_turno),
    path("ajax/subprogramas/", views.subprogramas_por_programa, name="subprogramas_por_programa"),
]
