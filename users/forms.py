from django import forms
from .models import Usuario

widgets = {
    'dni': forms.TextInput(attrs={'placeholder': 'XX.XXX.XXX'}),
}

class RegistroDocenteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirmar_password = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'dni', 'username', 'email', 'password', 'confirmar_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")
        if password and confirmar_password and password != confirmar_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.es_docente = True
        if commit:
            user.save()
        return user
    
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Usuario.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Ya existe un docente registrado con este DNI.")
        return dni

