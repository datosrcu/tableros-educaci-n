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

    # === MÚLTIPLES ALIAS PARA LA MISMA VISTA ===
    
    # Alias 1: Para docente (nombre específico)
    path(
        "docente/sala/<int:sala_id>/asistencias/imprimir/",
        views.imprimir_asistencias_sala,
        name="imprimir_asistencias_sala_docente",
    ),
    
    # Alias 2: Mismo nombre para docente (para compatibilidad)
    path(
        "docente/sala/<int:sala_id>/asistencias/imprimir/",
        views.imprimir_asistencias_sala,
        name="imprimir_asistencias_sala",  # ← Este alias capturará las llamadas sin _docente
    ),
    
    # Alias 3: Para coordinador
    path(
        "coordinador/asistencias/imprimir/<int:sala_id>/",
        views.imprimir_asistencias_sala,
        name="imprimir_asistencias_sala_coordinador",
    ),

    # Listado General (para coordinador)
    path(
        "coordinador/listado-general/",
        views.lista_alumnos,
        name="lista_alumnos",
    ),
    
    path(
        "coordinador/exportar-alumnos-completo/",
        views.exportar_alumnos_completo_csv,
        name="exportar_alumnos_completo_csv",
    ),
]