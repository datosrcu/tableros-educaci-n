from django import forms
from .models import EstructuraFormulario, CampoFormulario


class EstructuraFormularioForm(forms.ModelForm):
    class Meta:
        model = EstructuraFormulario
        fields = ["programa", "activo"]


class CampoFormularioForm(forms.ModelForm):
    class Meta:
        model = CampoFormulario
        fields = [
            "etiqueta",
            "nombre_interno",
            "tipo",
            "obligatorio",
            "orden",
            "opciones",
        ]

    def clean(self):
        cleaned = super().clean()

        tipo = cleaned.get("tipo")
        opciones = cleaned.get("opciones")

        if tipo == "select" and not opciones:
            raise forms.ValidationError(
                "Debe definir opciones separadas por coma."
            )

        return cleaned

class FormularioDinamico(forms.Form):
    def __init__(self, *args, estructura=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estructura = estructura

        if estructura:
            for campo in estructura.campos.all().order_by('orden'):
                self.agregar_campo(campo)

    def agregar_campo(self, campo):
        field_kwargs = {
            'label': campo.etiqueta,
            'required': campo.obligatorio,
        }

        if campo.tipo == 'texto':
            self.fields[campo.nombre_interno] = forms.CharField(**field_kwargs)
        
        elif campo.tipo == 'textarea':
            self.fields[campo.nombre_interno] = forms.CharField(
                widget=forms.Textarea, **field_kwargs
            )
            
        elif campo.tipo == 'numero':
            self.fields[campo.nombre_interno] = forms.IntegerField(**field_kwargs)
            
        elif campo.tipo == 'fecha':
            self.fields[campo.nombre_interno] = forms.DateField(
                widget=forms.DateInput(attrs={'type': 'date'}),
                **field_kwargs
            )
            
        elif campo.tipo == 'booleano':
            # CheckboxInput returns True/False/None. 
            # If required=True, it MUST be checked. 
            # Usually for "Yes/No" questions we might want required=False 
            # so unchecked means No, but let's stick to standard behavior.
            self.fields[campo.nombre_interno] = forms.BooleanField(**field_kwargs)

        elif campo.tipo == 'select':
            opciones = [
                (op.strip(), op.strip()) 
                for op in campo.opciones.split(',')
            ]
            self.fields[campo.nombre_interno] = forms.ChoiceField(
                choices=opciones, **field_kwargs
            )
