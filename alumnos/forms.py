from django import forms
from .models import Alumno, Tutor
from django.forms import inlineformset_factory


class AlumnoForm(forms.ModelForm):
    tutores_existentes = forms.ModelMultipleChoiceField(
        queryset=Tutor.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tutores ya registrados"
    )

    class Meta:
        model = Alumno
        fields = ['nombre', 'apellido', 'dni']

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
