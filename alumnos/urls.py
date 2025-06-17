from django.urls import path
from . import views

app_name = 'alumnos'

urlpatterns = [
    path('dashboard/', views.dashboard_docente, name='dashboard'),
    path('sala/<int:sala_id>/asistencia/', views.cargar_asistencia, name='cargar_asistencia'),
    path('alumno/<int:alumno_id>/', views.ver_alumno, name='ver_alumno'),
    path('sala/<int:sala_id>/alumnos/', views.alumnos_por_sala, name='alumnos_por_sala'),
    path('sala/<int:sala_id>/alumnos/agregar/', views.agregar_alumno, name='agregar_alumno'),
    path('sala/<int:sala_id>/ver_asistencias/', views.ver_asistencias, name='ver_asistencias'),
    path('alumno/<int:alumno_id>/editar/', views.editar_alumno, name='editar_alumno'),

]
