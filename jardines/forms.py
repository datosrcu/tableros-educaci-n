from django import forms
from .models import Sala, Subprograma, Jardin, Programa, AsistenciaDocente, LicenciaDocente

class AsistenciaDocenteForm(forms.ModelForm):
    class Meta:
        model = AsistenciaDocente
        fields = ["estado", "observaciones"]
        widgets = {
            "estado": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "observaciones": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Aclaraciones..."}),
        }


class JardinAdminForm(forms.ModelForm):
    class Meta:
        model = Jardin
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Al editar
        if self.instance.pk and self.instance.programa:
            self.fields["subprograma"].queryset = Subprograma.objects.filter(
                programa=self.instance.programa
            )
        else:
            self.fields["subprograma"].queryset = Subprograma.objects.none()
            
class SalaAdminForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        jardin = cleaned_data.get("jardin")
        turno = cleaned_data.get("turno")
        nombre = cleaned_data.get("nombre")

        # Validación anticipada (misma lógica que el modelo)
        if jardin and turno and nombre:
            qs = Sala.objects.filter(
                jardin=jardin,
                turno=turno,
                nombre__iexact=nombre,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Ya existe una sala con este nombre, turno y jardín."
                )

        return cleaned_data


class LicenciaDocenteForm(forms.ModelForm):
    class Meta:
        model = LicenciaDocente
        fields = [
            "docente",
            "tipo_licencia",
            "motivo",
            "fecha_desde",
            "fecha_hasta",
            "reemplazante",
        ]
        widgets = {
            "docente": forms.Select(attrs={"class": "form-select"}),
            "tipo_licencia": forms.Select(attrs={"class": "form-select"}),
            "motivo": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Escriba los motivos o detalles de la licencia..."}),
            "fecha_desde": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_hasta": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "reemplazante": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        from users.models import Usuario
        
        docentes_qs = Usuario.objects.filter(rol__in=["docente", "auxiliar"])
        
        if user and not user.es_admin() and user.programas_asignados.exists():
            programas = user.programas_asignados.all()
            from django.db.models import Q
            docentes_qs = docentes_qs.filter(
                Q(salas_asignadas__jardin__programa__in=programas)
            ).distinct()
            
        self.fields["docente"].queryset = docentes_qs.order_by("last_name", "first_name")
        self.fields["reemplazante"].queryset = docentes_qs.order_by("last_name", "first_name")
        self.fields["reemplazante"].required = False

