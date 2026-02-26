"""
Formularios para la administración y rendición del motor dinámico.
"""
from django import forms
from .models import EstructuraFormulario, CampoFormulario


class EstructuraFormularioForm(forms.ModelForm):
    """Gestión básica de la cabecera de estructura."""
    class Meta:
        model = EstructuraFormulario
        fields = ["programa", "activo"]


class CampoFormularioForm(forms.ModelForm):
    """
    Gestión de campos individuales. 
    Incluye validación específica para listas desplegables.
    """
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
        """Valida que los campos de tipo select tengan opciones definidas."""
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        opciones = cleaned.get("opciones")

        if tipo == "select" and not opciones:
            raise forms.ValidationError(
                "Debe definir opciones separadas por coma para campos de tipo 'Lista desplegable'."
            )

        return cleaned

class FormularioDinamico(forms.Form):
    """
    Motor reactivo que genera campos de Django en tiempo de ejecución.
    Se instancia con una 'estructura' y construye los campos basados en CampoFormulario.
    """
    def __init__(self, *args, estructura=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estructura = estructura

        if estructura:
            # Construir campos ordenados
            for campo in estructura.campos.all().order_by('orden'):
                self.agregar_campo(campo)

    def agregar_campo(self, campo):
        """Mapeo lógico de modelos de campo a widgets y validadores de Django."""
        field_kwargs = {
            'label': campo.etiqueta,
            'required': campo.obligatorio,
        }

        # 🏭 Fábrica de campos por tipo
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
            # Checkbox estándar
            self.fields[campo.nombre_interno] = forms.BooleanField(**field_kwargs)

        elif campo.tipo == 'select':
            # Parser de opciones separadas por coma
            opciones = [
                (op.strip(), op.strip()) 
                for op in campo.opciones.split(',')
            ]
            self.fields[campo.nombre_interno] = forms.ChoiceField(
                choices=opciones, **field_kwargs
            )
