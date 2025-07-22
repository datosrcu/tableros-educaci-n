from django import forms
from .models import Alumno, Tutor
from django.forms import inlineformset_factory
import re


class AlumnoForm(forms.ModelForm):

    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni', 'sala', 'tutores']
        exclude = ['sala']
        widgets = {
            'tutores': forms.CheckboxSelectMultiple
        }

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
        dni = self.cleaned_data.get('dni', '').strip()
        pattern = r'^\d{2}\.\d{3}\.\d{3}$'
        if not re.match(pattern, dni):
            raise forms.ValidationError("El DNI debe tener el formato XX.XXX.XXX")
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
        fields = ['nombre', 'apellido', 'dni', 'telefono', 'email']
