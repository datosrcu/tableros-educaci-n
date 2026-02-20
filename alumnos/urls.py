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
]
