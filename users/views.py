from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .decorators import solo_coordinador
from .forms import (
    CrearDocenteForm,
    EditarDocenteForm,
    AsignarDocentesSalaForm,
    JardinForm,
    ProgramaForm,
    SubprogramaForm,
    SalaForm,
)

from jardines.models import Jardin, Programa, Subprograma, Sala
from users.models import Usuario


# =====================================================
# DASHBOARD COORDINADOR
# =====================================================

@login_required
@solo_coordinador
def dashboard_coordinador(request):
    context = {
        "espacios_count": Jardin.objects.count(),
        "programas_count": Programa.objects.count(),
        "subprogramas_count": Subprograma.objects.count(),
        "salas_count": Sala.objects.count(),
        "docentes_count": Usuario.objects.filter(rol="docente").count(),
    }
    return render(request, "users/dashboard_coordinador.html", context)


# =====================================================
# LISTADOS
# =====================================================

@login_required
@solo_coordinador
def lista_espacios(request):
    espacios = Jardin.objects.all()
    return render(request, "users/lista_espacios.html", {"espacios": espacios})


@login_required
@solo_coordinador
def lista_programas(request):
    programas = Programa.objects.all()
    return render(request, "users/lista_programas.html", {"programas": programas})


@login_required
@solo_coordinador
def lista_subprogramas(request):
    subprogramas = Subprograma.objects.select_related("programa").all()
    return render(request, "users/lista_subprogramas.html", {"subprogramas": subprogramas})


@login_required
@solo_coordinador
def lista_salas(request):
    salas = Sala.objects.select_related("jardin").all()
    return render(request, "users/lista_salas.html", {"salas": salas})


@login_required
@solo_coordinador
def lista_docentes(request):
    docentes = Usuario.objects.filter(rol="docente")
    return render(request, "users/lista_docentes.html", {"docentes": docentes})


# =====================================================
# CREACIÓN
# =====================================================

@login_required
@solo_coordinador
def crear_jardin(request):
    if request.method == "POST":
        form = JardinForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:lista_espacios")
    else:
        form = JardinForm()

    return render(request, "users/espacios/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_jardin(request, jardin_id):
    jardin = get_object_or_404(Jardin, id=jardin_id)

    if request.method == "POST":
        form = JardinForm(request.POST, instance=jardin)
        if form.is_valid():
            form.save()
            return redirect("users:lista_espacios")
    else:
        form = JardinForm(instance=jardin)

    return render(
        request,
        "users/espacios/editar.html",
        {
            "form": form,
            "jardin": jardin
        }
    )


@login_required
@solo_coordinador
def crear_programa(request):
    if request.method == "POST":
        form = ProgramaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:lista_programas")
    else:
        form = ProgramaForm()

    return render(request, "users/programas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)
    if request.method == "POST":
        form = ProgramaForm(request.POST, instance=programa)
        if form.is_valid():
            form.save()
            return redirect("users:lista_programas")
    else:
        form = ProgramaForm(instance=programa)
    return render(request, "users/programas/editar.html", {"form": form, "programa": programa})


@login_required
@solo_coordinador
def crear_subprograma(request):
    if request.method == "POST":
        form = SubprogramaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:lista_subprogramas")
    else:
        form = SubprogramaForm()

    return render(request, "users/subprogramas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_subprograma(request, subprograma_id):
    subprograma = get_object_or_404(Subprograma, id=subprograma_id)
    if request.method == "POST":
        form = SubprogramaForm(request.POST, instance=subprograma)
        if form.is_valid():
            form.save()
            return redirect("users:lista_subprogramas")
    else:
        form = SubprogramaForm(instance=subprograma)
    return render(request, "users/subprogramas/editar.html", {"form": form, "subprograma": subprograma})


@login_required
@solo_coordinador
def crear_sala(request):
    if request.method == "POST":
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:lista_salas")
    else:
        form = SalaForm()

    return render(request, "users/salas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.method == "POST":
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            return redirect("users:lista_salas")
    else:
        form = SalaForm(instance=sala)
    return render(request, "users/salas/editar.html", {"form": form, "sala": sala})


@login_required
@solo_coordinador
def crear_docente(request):
    if request.method == "POST":
        form = CrearDocenteForm(request.POST)
        if form.is_valid():
            docente = form.save(commit=False)

            # 🔒 Blindaje: forzar rol docente
            docente.rol = "docente"

            # 🔒 Nunca permitir crear superuser desde web
            docente.is_superuser = False
            docente.is_staff = False

            docente.save()
            return redirect("users:lista_docentes")
    else:
        form = CrearDocenteForm()

    return render(request, "users/crear_docente.html", {"form": form})

@login_required
@solo_coordinador
def editar_docente(request, docente_id):
    docente = get_object_or_404(Usuario, id=docente_id)

    # 🔒 Seguridad adicional: solo editar docentes
    if docente.rol != "docente":
        raise PermissionDenied("Solo se pueden editar usuarios con rol docente.")

    if request.method == "POST":
        form = EditarDocenteForm(request.POST, instance=docente)
        if form.is_valid():
            form.save()
            return redirect("users:lista_docentes")
    else:
        form = EditarDocenteForm(instance=docente)

    return render(request, "users/editar_docente.html", {
        "form": form,
        "docente": docente
    })


# =====================================================
# ASIGNACIONES
# =====================================================

@login_required
@solo_coordinador
def asignar_docentes_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if request.method == "POST":
        form = AsignarDocentesSalaForm(request.POST, instance=sala)
        if form.is_valid():
            # 🔒 Validación defensiva
            docentes = form.cleaned_data["docentes"]
            for docente in docentes:
                if docente.rol != "docente":
                    raise PermissionDenied("Solo se pueden asignar usuarios con rol docente.")

            form.save()
            return redirect("users:lista_salas")
    else:
        form = AsignarDocentesSalaForm(instance=sala)

    return render(
        request,
        "users/asignar_docentes_sala.html",
        {
            "form": form,
            "sala": sala,
        },
    )


# =====================================================
# REDIRECCIÓN ADMIN
# =====================================================

@login_required
def admin_redirect(request):
    if request.user.rol == "docente":
        return redirect("alumnos:dashboard_docente")

    return redirect("/admin/")
