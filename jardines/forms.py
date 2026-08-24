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
            "turno_licencia",
            "fecha_desde",
            "fecha_hasta",
            "motivo",
        ]
        widgets = {
            "docente": forms.Select(attrs={"class": "form-select"}),
            "tipo_licencia": forms.Select(attrs={"class": "form-select"}),
            "turno_licencia": forms.Select(attrs={"class": "form-select"}),
            "fecha_desde": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_hasta": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "motivo": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Escriba los motivos o detalles de la licencia..."}),
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
        self.fields["docente"].empty_label = "Seleccione docente titular..."

        # Opciones de turno
        self.fields["turno_licencia"].choices = [
            ("", "Todos los turnos (Jornada completa)"),
            ("manana", "Turno Mañana"),
            ("tarde", "Turno Tarde"),
        ]
        self.fields["turno_licencia"].required = False

        # Ordenar alfabéticamente de forma ascendente las opciones de tipo de licencia
        tipo_choices = list(self.fields["tipo_licencia"].choices)
        empty_choice = [("", "Seleccione tipo de licencia...")]
        data_choices = sorted([c for c in tipo_choices if c[0]], key=lambda x: str(x[1]).lower())
        self.fields["tipo_licencia"].choices = empty_choice + data_choices


from .models import TipoActividadEspecial, ActividadEspecial

class TipoActividadEspecialForm(forms.ModelForm):
    class Meta:
        model = TipoActividadEspecial
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Festejo Especial, Taller..."}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Descripción opcional..."}),
        }


class ActividadEspecialForm(forms.ModelForm):
    class Meta:
        model = ActividadEspecial
        fields = [
            "nombre",
            "tipo",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "turno_afectado",
            "descripcion",
            "alcance",
            "programa",
            "jardin",
            "salas",
            "docentes",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Festejo Día de las Infancias, Jornada Pedagógica..."}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "turno_afectado": forms.Select(attrs={"class": "form-select"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Detalles adicionales de la actividad o motivo..."}),
            "alcance": forms.Select(attrs={"class": "form-select"}),
            "programa": forms.Select(attrs={"class": "form-select"}),
            "jardin": forms.Select(attrs={"class": "form-select"}),
            "salas": forms.SelectMultiple(attrs={"class": "form-select"}),
            "docentes": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        from users.models import Usuario
        from django.db.models.functions import Lower, Coalesce, NullIf
        from django.db.models import Value, Q

        # Tipos activos
        self.fields["tipo"].queryset = TipoActividadEspecial.objects.filter(activo=True).order_by("nombre")
        self.fields["tipo"].empty_label = "Seleccione un tipo de actividad..."

        # Querysets con filtros de jurisdicción para coordinadores
        programas_qs = Programa.objects.filter(activo=True)
        jardines_qs = Jardin.objects.all().order_by("nombre")
        salas_qs = Sala.objects.all().select_related("jardin").order_by("jardin__nombre", "nombre")
        docentes_qs = Usuario.objects.filter(rol__in=["docente", "auxiliar"])

        if user and not user.es_admin() and user.programas_asignados.exists():
            progs = user.programas_asignados.all()
            programas_qs = programas_qs.filter(id__in=progs.values_list('id', flat=True))
            jardines_qs = jardines_qs.filter(programa__in=progs)
            salas_qs = salas_qs.filter(jardin__programa__in=progs)
            docentes_qs = docentes_qs.filter(
                Q(salas_asignadas__jardin__programa__in=progs) |
                Q(programas_asignados__in=progs)
            ).distinct()

        self.fields["programa"].queryset = programas_qs.order_by("nombre")
        self.fields["programa"].required = False
        self.fields["programa"].empty_label = "Seleccione un programa..."

        self.fields["jardin"].queryset = jardines_qs
        self.fields["jardin"].required = False
        self.fields["jardin"].empty_label = "Seleccione un espacio / jardín..."

        self.fields["salas"].queryset = salas_qs
        self.fields["salas"].required = False

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

        self.fields["docentes"].queryset = docentes_qs
        self.fields["docentes"].label_from_instance = format_user_label
        self.fields["docentes"].required = False

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")
        alcance = cleaned_data.get("alcance")
        programa = cleaned_data.get("programa")
        jardin = cleaned_data.get("jardin")
        salas = cleaned_data.get("salas")
        docentes = cleaned_data.get("docentes")

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error("hora_fin", "El horario de fin debe ser posterior al horario de inicio.")

        if alcance == "programa" and not programa:
            self.add_error("programa", "Debe seleccionar un programa para el alcance 'Programa completo'.")
        elif alcance == "jardin" and not jardin:
            self.add_error("jardin", "Debe seleccionar un espacio para el alcance 'Espacio / Jardín'.")
        elif alcance == "sala" and not salas:
            self.add_error("salas", "Debe seleccionar al menos una sala para el alcance 'Salas específicas'.")
        elif alcance == "docente" and not docentes:
            self.add_error("docentes", "Debe seleccionar al menos un docente para el alcance 'Docentes puntuales'.")

        return cleaned_data



