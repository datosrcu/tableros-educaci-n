from django import forms
from .models import Sala, Subprograma, Jardin, Programa, AsistenciaDocente

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
