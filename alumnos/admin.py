from django.contrib import admin
from .models import Alumno, Asistencia, Tutor, MotivoJustificacion

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni_formateado', 'sala', 'activo', 'fecha_alta', 'fecha_baja')
    list_filter = ('sala', 'activo')
    search_fields = ('apellido','nombre', 'dni_formateado')
    filter_horizontal = ('tutores',)

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'fecha', 'estado', 'docente')
    list_filter = ('estado', 'fecha')
    search_fields = ('alumno__nombre', 'alumno_apellido',)

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni', 'telefono', 'email')
    search_fields = ('apellido', 'nombre', 'dni')

@admin.register(MotivoJustificacion)
class MotivoJustificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
# Register your models here.
