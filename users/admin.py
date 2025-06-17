from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

admin.site.register(Usuario, UserAdmin)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Datos adicionales', {'fields': ('dni', 'es_docente')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos adicionales', {'fields': ('dni', 'es_docente')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'dni_formateado', 'es_docente', 'is_staff', 'is_superuser')
    list_filter = ('es_docente', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'dni_formateado')
# Register your models here.
