from django.urls import path
from . import views

app_name = "jardines"

urlpatterns = [
    path("ajax/subprogramas/", views.cargar_subprogramas),
    path("ajax/jardines/", views.cargar_jardines),
    path("ajax/validar-docente-turno/", views.validar_docente_turno),
    path("ajax/subprogramas-por-programa/", views.subprogramas_por_programa, name="subprogramas_por_programa"),
    
    # Asistencia Docente
    path("asistencia/", views.lista_jardines_asistencia, name="lista_jardines_asistencia"),
    path("asistencia/jardin/<int:jardin_id>/", views.cargar_asistencia_docente, name="cargar_asistencia_docente"),
    path("asistencia/historial/", views.historial_asistencia_docente, name="historial_asistencia_docente"),
    path("asistencia/reporte-mensual/", views.reporte_asistencia_docente_mensual, name="reporte_asistencia_docente_mensual"),
]
