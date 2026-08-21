from django.contrib import admin
from .models import Programa, Subprograma, Jardin, Sala, AsignacionDocenteSala
from .forms import SalaAdminForm, JardinAdminForm
from users.admin_permissions import es_admin, es_directivo


class BaseAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_view_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_add_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_change_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == "administrador"

@admin.register(Programa)
class ProgramaAdmin(BaseAdmin):
    list_display = ('id', 'nombre', 'prefijo_comprobante', 'usa_formulario_ampliado', 'activo')
    list_display_links = ('id', 'nombre')
    list_editable = ('prefijo_comprobante', 'activo')
    search_fields = ('nombre',)
    list_filter = ('usa_formulario_ampliado','activo',)
    ordering = ('nombre',)
    
    def has_module_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_change_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_add_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == "administrador"

@admin.register(Subprograma)
class SubprogramaAdmin(BaseAdmin):
    list_display = ('id', 'nombre', 'usa_formulario_ampliado', 'programa')
    list_display_links = ('id', 'nombre')
    list_filter = ('programa', 'usa_formulario_ampliado')
    search_fields = ('nombre',)
    ordering = ('programa__nombre', 'nombre')
    
    def has_module_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_change_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_add_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == "administrador"


@admin.register(Jardin)
class EspacioAdmin(BaseAdmin):
    form = JardinAdminForm
    list_display = (
        'id',
        'nombre',
        'programa',
        'subprograma',
        'direccion',
    )
    list_display_links = ('id', 'nombre')

    list_filter = ('programa', 'subprograma')
    search_fields = ('nombre', 'direccion')
    ordering = ('programa__nombre', 'nombre')

    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'direccion')
        }),
        ('Programa educativo', {
            'fields': ('programa', 'subprograma')
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_change_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_add_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == "administrador"
    class Media:
        js = ("jardines/subprogramas_admin.js",)

class AsignacionDocenteSalaInline(admin.TabularInline):
    model = AsignacionDocenteSala
    extra = 1

@admin.register(Sala)
class SalaAdmin(BaseAdmin):
    form = SalaAdminForm
    list_display = (
        'id',
        'nombre',
        'jardin',
        'turno',
        'docentes_count',
    )
    list_display_links = ('id', 'nombre')

    list_filter = ('turno', 'jardin')
    search_fields = ('nombre', 'jardin__nombre')
    inlines = [AsignacionDocenteSalaInline]

    def docentes_count(self, obj):
        return obj.docentes.count()
    docentes_count.short_description = 'Docentes'
    
    def has_module_permission(self, request):
        return es_admin(request.user) or es_directivo(request.user)

    class Media:
        js = ("jardines/admin/sala.js",)


from .models import AsistenciaDocente
from django.utils.translation import gettext_lazy as _

@admin.action(description=_("Desfichar (Restablecer botón de asistencia)"))
def restablecer_fichada(modeladmin, request, queryset):
    # Reset fichado to False, clear coordinates and hora_ingreso
    updated = queryset.update(fichado=False, hora_ingreso=None, latitude=None, longitude=None, estado='A', observaciones='Restablecido por administrador.')
    modeladmin.message_user(request, f"Se restablecieron {updated} registros de asistencia.")

@admin.register(AsistenciaDocente)
class AsistenciaDocenteAdmin(BaseAdmin):
    list_display = ('id', 'docente', 'jardin', 'turno', 'fecha', 'fichado', 'estado', 'hora_ingreso')
    list_display_links = ('id', 'docente')
    list_filter = ('fecha', 'fichado', 'estado', 'turno', 'jardin')
    search_fields = ('docente__username', 'docente__first_name', 'docente__last_name', 'jardin__nombre')
    ordering = ('-fecha', 'docente__last_name')
    actions = [restablecer_fichada]
    
    def has_module_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_change_permission(self, request, obj=None):
        return request.user.rol in ["administrador", "coordinador"]

    def has_add_permission(self, request):
        return request.user.rol in ["administrador", "coordinador"]

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == "administrador"


from .models import TipoActividadEspecial, ActividadEspecial

@admin.register(TipoActividadEspecial)
class TipoActividadEspecialAdmin(BaseAdmin):
    list_display = ('id', 'nombre', 'es_default', 'activo')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('es_default', 'activo')


@admin.register(ActividadEspecial)
class ActividadEspecialAdmin(BaseAdmin):
    list_display = ('id', 'nombre', 'tipo', 'fecha', 'hora_inicio', 'hora_fin', 'alcance', 'creado_por')
    list_filter = ('tipo', 'fecha', 'alcance')
    search_fields = ('nombre', 'descripcion', 'tipo__nombre')
    filter_horizontal = ('salas', 'docentes')

