from django import forms
from .models import Alumno, Tutor, Inscripcion, FichaProgramaAlumno
from django.forms import inlineformset_factory
import re


class AlumnoForm(forms.ModelForm):

    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni', 'fecha_nacimiento', 'tutores']
        widgets = {
            'tutores': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔹 Ordenar tutores alfabéticamente A-Z
        self.fields['tutores'].queryset = Tutor.objects.all().order_by('apellido', 'nombre')
        # 🔹 Asegurar que fecha_nacimiento sea obligatoria en el formulario
        self.fields['fecha_nacimiento'].required = True
        self.fields['fecha_nacimiento'].help_text = "Formato: DD/MM/AAAA"

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if not apellido:
            raise forms.ValidationError("El apellido es obligatorio.")
        return apellido

    def clean_dni(self):
        dni = self.cleaned_data["dni"]
        if len(dni) < 7:
            raise forms.ValidationError("El DNI es demasiado corto.")
        return dni
class EditarAlumnoForm(forms.ModelForm):
    tutores = forms.ModelMultipleChoiceField(
        queryset=Tutor.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tutores"
    )

    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni', 'tutores']

class TutorForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['nombre', 'apellido', 'dni', 'telefono']

class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = "__all__"

class FichaProgramaAlumnoForm(forms.ModelForm):
    class Meta:
        model = FichaProgramaAlumno
        exclude = ("alumno",)
        widgets = {
            'sabe_leer': forms.Select(choices=[('', '---------'), (True, 'Sí'), (False, 'No')]),
            'sabe_escribir': forms.Select(choices=[('', '---------'), (True, 'Sí'), (False, 'No')]),
            'asistencia_social': forms.Select(choices=[('', '---------'), (True, 'Sí'), (False, 'No')]),
        }
        
    def clean_telefono(self):
        tel = self.cleaned_data.get("telefono", "")
        if tel and not tel.replace("+", "").replace(" ", "").isdigit():
            raise forms.ValidationError("El teléfono solo puede contener números.")
        return tel    