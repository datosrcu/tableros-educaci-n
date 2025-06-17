from django.contrib import admin
from .models import Jardin, Sala

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'jardin', 'turno')
    list_filter = ('jardin', 'turno')
    filter_horizontal = ('docentes',)

admin.site.register(Jardin)

# Register your models here.
