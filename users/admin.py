from django.contrib import admin
from .models import Usuario
from .admin_permissions import es_admin


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "rol", "is_active")
    list_filter = ("rol", "is_active")

    def has_module_permission(self, request):
        return es_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return es_admin(request.user)

    def has_add_permission(self, request):
        return es_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return es_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return es_admin(request.user)

# Register your models here.
