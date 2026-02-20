from django.contrib import admin
from .models import Usuario
from django.contrib.auth.admin import UserAdmin


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    
    list_display = ("username", "email", "rol", "is_staff")
    list_filter = ("rol",)
    search_fields = ("username", "email")
    
    fieldsets = (
        ("Credenciales", {
            "fields": ("username", "password")
        }),
        ("Información personal", {
            "fields": ("first_name", "last_name", "email")
        }),
        ("Rol y permisos", {
            "fields": ("rol", "is_active", "is_staff", "is_superuser")
        }),
    )



    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Coordinador NO ve administradores ni otros coordinadores
        if request.user.rol == "coordinador":
            return qs.filter(rol="docente")

        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Coordinador SOLO puede crear docentes
        if request.user.rol == "coordinador":
            form.base_fields["rol"].choices = [
                ("docente", "Docente"),
            ]

        return form

    def has_delete_permission(self, request, obj=None):
        if request.user.rol == "coordinador":
            return False
        return True

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.rol in ['administrador', 'coordinador']

    def has_view_permission(self, request, obj=None):
        return request.user.rol in ['administrador', 'coordinador']

    def has_add_permission(self, request):
        return request.user.rol == 'coordinador' or request.user.rol == 'administrador'

    def has_change_permission(self, request, obj=None):
        return request.user.rol == 'coordinador' or request.user.rol == 'administrador'

    def has_delete_permission(self, request, obj=None):
        return request.user.rol == 'administrador'


# Register your models here.
