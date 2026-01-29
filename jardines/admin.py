from django.contrib import admin
from .models import Programa, Subprograma, Jardin, Sala
from .forms import SalaAdminForm, JardinAdminForm
from users.admin_permissions import es_admin, es_directivo


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)
    ordering = ('nombre',)
    
    def has_module_permission(self, request):
        return es_admin(request.user) or es_directivo(request.user)

@admin.register(Subprograma)
class SubprogramaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'programa')
    list_filter = ('programa',)
    search_fields = ('nombre',)
    ordering = ('programa__nombre', 'nombre')
    
    def has_module_permission(self, request):
        return es_admin(request.user) or es_directivo(request.user)


@admin.register(Jardin)
class JardinAdmin(admin.ModelAdmin):
    form = JardinAdminForm
    list_display = (
        'id',
        'nombre',
        'programa',
        'subprograma',
        'direccion',
    )

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
        return es_admin(request.user) or es_directivo(request.user)
    class Media:
        js = ("jardines/js/jardin_admin.js",)

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    form = SalaAdminForm
    list_display = (
        'id',
        'nombre',
        'jardin',
        'turno',
        'docentes_count',
    )

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
