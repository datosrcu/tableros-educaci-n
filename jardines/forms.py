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
        from django.db.models.functions import Lower, Coalesce, NullIf
        from django.db.models import Value
        
        docentes_qs = Usuario.objects.filter(rol__in=["docente", "auxiliar"])
        
        if user and not user.es_admin() and user.programas_asignados.exists():
            programas = user.programas_asignados.all()
            from django.db.models import Q
            docentes_qs = docentes_qs.filter(
                Q(salas_asignadas__jardin__programa__in=programas)
            ).distinct()
            
        docentes_qs = docentes_qs.order_by(
            Coalesce(NullIf(Lower("last_name"), Value("")), NullIf(Lower("first_name"), Value("")), Lower("username")).asc(),
            Lower("first_name").asc(nulls_last=True),
            Lower("username").asc()
        )
        
        def format_user_label(obj):
            if obj.last_name and obj.first_name:
                return f"{obj.last_name}, {obj.first_name}"
            elif obj.last_name or obj.first_name:
                return f"{obj.last_name or obj.first_name}"
            return obj.username

        self.fields["docente"].queryset = docentes_qs
        self.fields["docente"].label_from_instance = format_user_label
        self.fields["docente"].empty_label = ""

        self.fields["reemplazante"].queryset = docentes_qs
        self.fields["reemplazante"].label_from_instance = format_user_label
        self.fields["reemplazante"].empty_label = ""
        self.fields["reemplazante"].required = False

        # Ordenar alfabéticamente de forma ascendente las opciones de tipo de licencia
        tipo_choices = list(self.fields["tipo_licencia"].choices)
        empty_choice = [c for c in tipo_choices if not c[0]]
        data_choices = sorted([c for c in tipo_choices if c[0]], key=lambda x: str(x[1]).lower())
        self.fields["tipo_licencia"].choices = empty_choice + data_choices


