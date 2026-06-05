from django.contrib import admin
from .models import ProgramaCobro, ResponsableCobro, Pago

@admin.register(ProgramaCobro)
class ProgramaCobroAdmin(admin.ModelAdmin):
    list_display = ("programa", "importe_mensual", "activo")
    list_filter = ("activo",)
    search_fields = ("programa__nombre",)
    list_editable = ("importe_mensual", "activo")


@admin.register(ResponsableCobro)
class ResponsableCobroAdmin(admin.ModelAdmin):
    list_display = ("usuario", "programa", "rol")
    list_filter = ("rol", "programa")
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "programa__nombre",
    )


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "alumno",
        "programa",
        "subprograma",
        "sala",
        "importe",
        "fecha_pago",
        "metodo_pago",
        "estado",
        "registrado_por",
        "created_at",
    )
    list_filter = ("estado", "metodo_pago", "fecha_pago", "programa")
    search_fields = (
        "alumno__nombre",
        "alumno__apellido",
        "alumno__dni",
        "registrado_por__username",
        "registrado_por__first_name",
        "registrado_por__last_name",
    )
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)
