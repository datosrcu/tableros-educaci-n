from django.contrib import admin
from .models import Programa, Subprograma, Jardin, Turno, Sala, Usuario, Alumno, AsignacionSala, Asistencia

@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Subprograma)
class SubprogramaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'programa')
    list_filter = ('programa',)
    search_fields = ('nombre',)

@admin.register(Jardin)
class JardinAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'sector', 'programa', 'subprograma')
    list_filter = ('sector', 'programa')
    search_fields = ('nombre', 'direccion')

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'jardin', 'turno')
    list_filter = ('jardin', 'turno')
    search_fields = ('nombre',)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'rol')
    list_filter = ('rol',)
    search_fields = ('nombre', 'dni')

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'fecha_nacimiento')
    search_fields = ('nombre', 'dni')

@admin.register(AsignacionSala)
class AsignacionSalaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'sala', 'fecha_ingreso', 'activo')
    list_filter = ('activo', 'sala__jardin')

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'sala', 'fecha', 'presente')
    list_filter = ('presente', 'fecha', 'sala__jardin')
