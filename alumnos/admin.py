from django.contrib import admin
from .models import Alumno, Asistencia, Tutor, MotivoJustificacion, AsignacionSala

class AdminSoloStaffPorRol(admin.ModelAdmin):
    ROLES_PERMITIDOS = ["administrador", "coordinador"]

    def _permitido(self, request):
        return request.user.is_authenticated and request.user.rol in self.ROLES_PERMITIDOS

    def has_module_permission(self, request):
        return self._permitido(request)

    def has_view_permission(self, request, obj=None):
        return self._permitido(request)

    def has_add_permission(self, request):
        return self._permitido(request)

    def has_change_permission(self, request, obj=None):
        return self._permitido(request)

    def has_delete_permission(self, request, obj=None):
        return self._permitido(request)

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni')
    search_fields = ('apellido','nombre', 'dni')

@admin.register(AsignacionSala)
class AsignacionSalaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'sala', 'activo', 'fecha_ingreso', 'fecha_baja')
    list_filter = ('sala', 'activo')
    search_fields = ('alumno__apellido', 'alumno__nombre')

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = (
        'alumno',
        'fecha',
        'estado',
        'motivo_resumido',
    )

    list_filter = ('estado', 'fecha', 'sala')
    search_fields = ('alumno__nombre',)
    ordering = ('-fecha',)

    def motivo_resumido(self, obj):
        if obj.motivo:
            return obj.motivo[:40]
        return '-'
    motivo_resumido.short_description = 'Motivo'


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'dni', 'telefono', 'email')
    search_fields = ('apellido', 'nombre', 'dni')

@admin.register(MotivoJustificacion)
class MotivoJustificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
# Register your models here.
