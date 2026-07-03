from django import forms
from django.core.exceptions import ValidationError

from .models import Usuario
from jardines.models import Jardin, Programa, Subprograma, Sala, AsignacionDocenteSala


# =====================================================
# USUARIO ADMIN FORM (USAR SOLO EN ADMIN)
# =====================================================

class UsuarioAdminForm(forms.ModelForm):

    class Meta:
        model = Usuario
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # 🔒 Coordinador solo puede crear docentes
        if request and request.user.rol == "coordinador":
            self.fields["rol"].choices = [
                ("docente", "Docente"),
            ]

    def clean_rol(self):
        rol = self.cleaned_data.get("rol")

        # 🔒 Nunca permitir escalamiento por form
        if rol not in ["docente", "coordinador", "administrador"]:
            raise ValidationError("Rol inválido.")

        return rol


# =====================================================
# CREAR DOCENTE (USADO EN WEB)
# =====================================================

class CrearDocenteForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "dni", "telefono", "username", "email", "password"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "dni": "DNI / Pasaporte",
            "telefono": "Teléfono"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["dni"].required = True

    def clean_dni(self):
        dni = self.cleaned_data.get("dni")
        if dni:
            if not dni.isdigit():
                 raise ValidationError("El DNI debe contener solo números.")
            if Usuario.objects.filter(dni=dni).exists():
                 raise ValidationError("Ya existe un usuario con este DNI.")
        return dni

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Ya existe un usuario con ese nombre.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con ese email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        # 🔒 Forzar seguridad
        user.set_password(self.cleaned_data["password"])
        user.rol = "docente"
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

        return user


# =====================================================
# EDITAR DOCENTE
# =====================================================

class EditarDocenteForm(forms.ModelForm):

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "dni", "telefono", "username", "email", "is_active"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "dni": "DNI / Pasaporte",
            "telefono": "Teléfono",
            "is_active": "Activo"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["dni"].required = True

    def clean_dni(self):
        dni = self.cleaned_data.get("dni")
        if dni:
            if not dni.isdigit():
                 raise ValidationError("El DNI debe contener solo números.")
            
            # Excluir al usuario actual de la validación de unicidad
            qs = Usuario.objects.filter(dni=dni)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                 raise ValidationError("Ya existe otro usuario con este DNI.")
        return dni

    def clean_username(self):
        username = self.cleaned_data.get("username")
        
        qs = Usuario.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Ya existe otro usuario con ese nombre.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = Usuario.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError("Ya existe otro usuario con ese email.")
        return email
# =====================================================
# ASIGNAR DOCENTES A SALA
# =====================================================

class AsignarDocentesSalaForm(forms.ModelForm):

    docentes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Docentes asignados"
    )

    class Meta:
        model = Sala
        fields = ("docentes",)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # 🔒 Queryset dinámico
        qs = Usuario.objects.filter(rol="docente", is_active=True)
        if user and not user.es_admin():
            from django.db.models import Q
            qs = qs.filter(
                Q(salas_asignadas__jardin__programa__in=user.programas_asignados.all()) |
                Q(salas_asignadas__isnull=True)
            ).distinct()
        self.fields["docentes"].queryset = qs


    def clean_docentes(self):
        docentes = self.cleaned_data.get("docentes")

        for docente in docentes:
            if docente.rol != "docente":
                raise ValidationError(
                    "Solo usuarios con rol docente pueden asignarse."
                )

        return docentes


# =====================================================
# JARDIN
# =====================================================

class JardinForm(forms.ModelForm):
    class Meta:
        model = Jardin
        fields = (
            "programa",
            "subprograma",
            "nombre",
            "direccion",
            "telefono",
            "coordenadas",
            "sector",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and not user.es_admin() and user.programas_asignados.exists():
            programas = user.programas_asignados.all()
            if "programa" in self.fields:
                self.fields["programa"].queryset = Programa.objects.filter(id__in=programas)
            if "subprograma" in self.fields:
                self.fields["subprograma"].queryset = Subprograma.objects.filter(programa__in=programas)


# =====================================================
# PROGRAMA
# =====================================================

class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = (
            "nombre",
            "descripcion",
            "usa_formulario_ampliado",
            "activo",
        )


# =====================================================
# SUBPROGRAMA
# =====================================================

class SubprogramaForm(forms.ModelForm):
    class Meta:
        model = Subprograma
        fields = (
            "programa",
            "nombre",
            "usa_formulario_ampliado",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and not user.es_admin() and user.programas_asignados.exists():
            programas = user.programas_asignados.all()
            if "programa" in self.fields:
                self.fields["programa"].queryset = Programa.objects.filter(id__in=programas)


# =====================================================
# SALA
# =====================================================

class SalaForm(forms.ModelForm):
    docentes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(rol="docente", is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Docentes"
    )

    class Meta:
        model = Sala
        fields = (
            "jardin",
            "subprograma",
            "nombre",
            "turno",
            "horario_inicio",
            "horario_fin",
            "responsable",
        )
        labels = {
            "responsable": "Docente",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        # Cargar docentes asignados inicialmente
        if self.instance and self.instance.pk:
            self.initial["docentes"] = self.instance.docentes.all()

        # Filtrar responsables y docentes a los de la jurisdicción del coordinador
        if user and not user.es_admin() and user.programas_asignados.exists():
            programas = user.programas_asignados.all()
            if "jardin" in self.fields:
                self.fields["jardin"].queryset = Jardin.objects.filter(programa__in=programas)
            if "subprograma" in self.fields:
                self.fields["subprograma"].queryset = Subprograma.objects.filter(programa__in=programas)
            
            from django.db.models import Q as Qlocal
            self.fields["responsable"].queryset = Usuario.objects.filter(
                rol__in=["docente", "coordinador"]
            ).filter(
                Qlocal(salas_asignadas__jardin__programa__in=programas) |
                Qlocal(programas_asignados__in=programas) |
                Qlocal(rol="docente", salas_asignadas__isnull=True)
            ).distinct()
            
            self.fields["docentes"].queryset = Usuario.objects.filter(rol="docente", is_active=True).filter(
                Qlocal(salas_asignadas__jardin__programa__in=programas) |
                Qlocal(programas_asignados__in=programas) |
                Qlocal(salas_asignadas__isnull=True)
            ).distinct()

    def clean_docentes(self):
        docentes = self.cleaned_data.get("docentes")
        if docentes:
            for docente in docentes:
                if docente.rol != "docente":
                    raise ValidationError(
                        "Solo usuarios con rol docente pueden asignarse."
                    )
        return docentes

    def clean_responsable(self):
        responsable = self.cleaned_data.get("responsable")

        if responsable and responsable.rol not in ["docente", "coordinador"]:
            raise ValidationError(
                "El responsable debe ser docente o coordinador."
            )

        return responsable

    def save(self, commit=True):
        sala = super().save(commit=False)
        if commit:
            sala.save()
            self.save_docentes(sala)
        else:
            original_save_m2m = self.save_m2m
            def custom_save_m2m():
                original_save_m2m()
                self.save_docentes(sala)
            self.save_m2m = custom_save_m2m
        return sala

    def save_docentes(self, sala):
        new_docentes = self.cleaned_data.get("docentes", [])
        # Eliminar docentes desasignados (evaluando los IDs en memoria para evitar el error 1093 de MySQL)
        ids_a_eliminar = list(sala.asignaciones_docentes.exclude(docente__in=new_docentes).values_list('id', flat=True))
        if ids_a_eliminar:
            sala.asignaciones_docentes.filter(id__in=ids_a_eliminar).delete()
        # Crear asignaciones para nuevos docentes (con días por defecto basados en la sala)
        for docente in new_docentes:
            AsignacionDocenteSala.objects.get_or_create(
                sala=sala,
                docente=docente,
                defaults={
                    "lunes": sala.lunes,
                    "martes": sala.martes,
                    "miercoles": sala.miercoles,
                    "jueves": sala.jueves,
                    "viernes": sala.viernes,
                    "sabado": sala.sabado,
                    "domingo": sala.domingo,
                }
            )


# =====================================================
# RESTABLECER PASSWORD
# =====================================================

class RestablecerPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control rounded-pill"}),
        label="Nueva Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control rounded-pill"}),
        label="Confirmar Contraseña"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data
