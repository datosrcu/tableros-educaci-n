from django import forms
from .models import Pago, MESES_NOMBRES
from django.utils import timezone

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = [
            "alumno",
            "programa",
            "importe",
            "fecha_pago",
            "metodo_pago",
            "estado",
            "mes_pagado",
            "anio_pagado",
            "enviar_correo",
            "correo_envio",
            "observaciones",
        ]
        widgets = {
            "alumno": forms.HiddenInput(),
            "programa": forms.HiddenInput(),
            "importe": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "fecha_pago": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "mes_pagado": forms.Select(attrs={"class": "form-select"}),
            "anio_pagado": forms.Select(attrs={"class": "form-select"}),
            "enviar_correo": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "enviar_correo_checkbox"}),
            "correo_envio": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com", "id": "correo_envio_input"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        initial_alumno = kwargs.get("initial", {}).get("alumno")
        initial_programa = kwargs.get("initial", {}).get("programa")
        initial_importe = kwargs.get("initial", {}).get("importe")
        initial_correo = kwargs.get("initial", {}).get("correo_envio")
        
        super().__init__(*args, **kwargs)
        
        # Opciones de año dinámicas (Año actual - 2 hasta Año actual + 2)
        current_year = timezone.now().year
        year_choices = [(y, str(y)) for y in range(current_year - 2, current_year + 3)]
        self.fields["anio_pagado"].widget.choices = year_choices
        
        if not self.instance.pk:
            self.fields["fecha_pago"].initial = timezone.now().date()
            self.fields["mes_pagado"].initial = timezone.now().month
            self.fields["anio_pagado"].initial = current_year
            if initial_importe:
                self.fields["importe"].initial = initial_importe
            if initial_correo:
                self.fields["correo_envio"].initial = initial_correo

        # Campos visuales de solo lectura
        self.fields["alumno_text"] = forms.CharField(
            initial=str(initial_alumno) if initial_alumno else (str(self.instance.alumno) if self.instance.pk else ""),
            required=False,
            disabled=True,
            label="Alumno",
            widget=forms.TextInput(attrs={"class": "form-control-plaintext fw-bold"})
        )
        self.fields["programa_text"] = forms.CharField(
            initial=str(initial_programa) if initial_programa else (str(self.instance.programa) if self.instance.pk else ""),
            required=False,
            disabled=True,
            label="Programa",
            widget=forms.TextInput(attrs={"class": "form-control-plaintext fw-bold"})
        )
        
        # Reordenar campos
        field_order = [
            "alumno_text",
            "programa_text",
            "alumno",
            "programa",
            "importe",
            "fecha_pago",
            "metodo_pago",
            "estado",
            "mes_pagado",
            "anio_pagado",
            "enviar_correo",
            "correo_envio",
            "observaciones"
        ]
        self.fields = {key: self.fields[key] for key in field_order if key in self.fields}
        
    def clean(self):
        cleaned_data = super().clean()
        enviar = cleaned_data.get("enviar_correo")
        correo = cleaned_data.get("correo_envio")
        
        if enviar and not correo:
            self.add_error("correo_envio", "Debe ingresar un correo electrónico si activa la opción de envío.")
            
        return cleaned_data


