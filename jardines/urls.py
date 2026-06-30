from django.urls import path
from . import views
from . import views_licencias

app_name = "jardines"

urlpatterns = [
    path("ajax/subprogramas/", views.cargar_subprogramas),
    path("ajax/jardines/", views.cargar_jardines),
    path("ajax/validar-docente-turno/", views.validar_docente_turno),
    path("ajax/subprogramas-por-programa/", views.subprogramas_por_programa, name="subprogramas_por_programa"),
    # Dashboard Espacios Lúdicos
    path("dashboard-espacios-ludicos/", views.DashboardEspaciosLudicosView.as_view(), name="dashboard_espacios_ludicos"),
    
    # Asistencia Docente
    path("asistencia/", views.lista_jardines_asistencia, name="lista_jardines_asistencia"),
    path("asistencia/jardin/<int:jardin_id>/", views.cargar_asistencia_docente, name="cargar_asistencia_docente"),
    path("asistencia/historial/", views.historial_asistencia_docente, name="historial_asistencia_docente"),
    path("asistencia/reporte-mensual/", views.reporte_asistencia_docente_mensual, name="reporte_asistencia_docente_mensual"),
    path("asistencia/resumen-diario/", views.resumen_actividad_docente, name="resumen_actividad_docente"),
    path("asistencia/registrar-fichada/", views.registrar_asistencia_docente, name="registrar_asistencia_docente"),

    # Licencias Docentes
    path("licencias/", views_licencias.lista_licencias, name="lista_licencias"),
    path("licencias/crear/", views_licencias.crear_licencia, name="crear_licencia"),
    path("licencias/<int:pk>/", views_licencias.ver_detalle_licencia, name="ver_detalle_licencia"),
    path("licencias/<int:pk>/editar/", views_licencias.editar_licencia, name="editar_licencia"),
    path("licencias/<int:pk>/eliminar/", views_licencias.eliminar_licencia, name="eliminar_licencia"),
    path("licencias/exportar/", views_licencias.exportar_licencias_excel, name="exportar_licencias"),
    path("licencias/reporte/", views_licencias.reporte_licencias, name="reporte_licencias"),
]

