from django.urls import path
from . import views

app_name = "users"

urlpatterns = [

    # Dashboard
    path(
        "coordinador/",
        views.dashboard_coordinador,
        name="dashboard_coordinador",
    ),

    # Programas
    path(
        "coordinador/programas/",
        views.lista_programas,
        name="lista_programas",
    ),
    path(
        "coordinador/programas/nuevo/",
        views.crear_programa,
        name="crear_programa",
    ),
    path(
        "coordinador/programas/<int:programa_id>/editar/",
        views.editar_programa,
        name="editar_programa",
    ),

    # Subprogramas
    path(
        "coordinador/subprogramas/",
        views.lista_subprogramas,
        name="lista_subprogramas",
    ),
    path(
        "coordinador/subprogramas/nuevo/",
        views.crear_subprograma,
        name="crear_subprograma",
    ),
    path(
        "coordinador/subprogramas/<int:subprograma_id>/editar/",
        views.editar_subprograma,
        name="editar_subprograma",
    ),

    # Espacios (Jardines)
    path(
        "coordinador/espacios/",
        views.lista_espacios,
        name="lista_espacios",
    ),
    path(
        "coordinador/espacios/nuevo/",
        views.crear_jardin,
        name="crear_espacio",
    ),

    path(
        "coordinador/espacios/<int:jardin_id>/editar/",
        views.editar_jardin,
        name="editar_jardin",
    ),
    # Salas
    path(
        "coordinador/salas/",
        views.lista_salas,
        name="lista_salas",
    ),
    path(
        "coordinador/salas/nuevo/",
        views.crear_sala,
        name="crear_sala",
    ),
    path(
        "coordinador/salas/<int:sala_id>/editar/",
        views.editar_sala,
        name="editar_sala",
    ),

    # Docentes
    path(
        "coordinador/docentes/",
        views.lista_docentes,
        name="lista_docentes",
    ),
    path(
        "coordinador/docentes/nuevo/",
        views.crear_docente,
        name="crear_docente",
    ),
    path(
        "coordinador/docentes/<int:docente_id>/editar/",
        views.editar_docente,
        name="editar_docente",
    ),
    path(
        "coordinador/salas/<int:sala_id>/asignar-docentes/",
        views.asignar_docentes_sala,
        name="asignar_docentes_sala",
    ),
]


