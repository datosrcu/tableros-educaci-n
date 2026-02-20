from django.urls import path
from . import views

app_name = "alumnos"

urlpatterns = [

    # Dashboard
    path(
        "docente/",
        views.dashboard_docente,
        name="dashboard_docente",
    ),

    # Sala
    path(
        "docente/sala/<int:sala_id>/",
        views.alumnos_por_sala,
        name="alumnos_por_sala",
    ),

    # Asistencia
    path(
        "docente/sala/<int:sala_id>/asistencia/",
        views.cargar_asistencia,
        name="cargar_asistencia",
    ),

    # Alumnos
    path(
        "docente/alumno/<int:alumno_id>/",
        views.detalle_alumno,
        name="detalle_alumno",
    ),

    path(
        "docente/alumno/<int:alumno_id>/editar/",
        views.editar_alumno,
        name="editar_alumno",
    ),

    path(
        "docente/sala/<int:sala_id>/alumno/nuevo/",
        views.agregar_alumno,
        name="agregar_alumno",
    ),
    path(
        "tutor/nuevo/ajax/",
        views.crear_tutor_ajax,
        name="crear_tutor_ajax",
    ),
    path(
        "docente/sala/<int:sala_id>/asistencias/",
        views.ver_asistencias,
        name="ver_asistencias",
    ),

    # Exportación e Impresión
    path(
        "docente/sala/<int:sala_id>/alumnos/csv/",
        views.exportar_alumnos_csv,
        name="exportar_alumnos_csv",
    ),
    path(
        "docente/sala/<int:sala_id>/alumnos/imprimir/",
        views.imprimir_alumnos_sala,
        name="imprimir_alumnos_sala",
    ),
    path(
        "docente/sala/<int:sala_id>/asistencias/csv/",
        views.exportar_asistencias_csv,
        name="exportar_asistencias_csv",
    ),
    path(
        "docente/sala/<int:sala_id>/asistencias/imprimir/",
        views.imprimir_asistencias_sala,
        name="imprimir_asistencias_sala",
    ),
]
