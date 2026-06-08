from django.contrib import admin
from .models import Programa, Subprograma, Jardin, Sala
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
    filter_horizontal = ('docentes',)

    def docentes_count(self, obj):
        return obj.docentes.count()
    docentes_count.short_description = 'Docentes'
    
    def has_module_permission(self, request):
        return es_admin(request.user) or es_directivo(request.user)

    class Media:
        js = ("jardines/admin/sala.js",)

# Register your models here.
