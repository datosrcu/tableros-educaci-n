import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import ProtectedError

from .decorators import solo_coordinador
from .forms import (
    JardinForm,
    ProgramaForm,
    SubprogramaForm,
    SalaForm,
    CrearDocenteForm,
    EditarDocenteForm,
    AsignarDocentesSalaForm,
    RestablecerPasswordForm,
)

from jardines.models import Jardin, Programa, Subprograma, Sala
from alumnos.models import Alumno, Asistencia
from users.models import Usuario, AccionAuditoria


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
    
    if request.user.rol == "coordinator" or request.user.rol == "coordinador":
        return redirect("users:dashboard_coordinador")

    return redirect("/admin/")

class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AccionAuditoria
    template_name = "users/audit_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def test_func(self):
        return self.request.user.es_coordinador() or self.request.user.es_admin()

    def get_queryset(self):
        # Coordinadores y administradores ven todo el log.
        # Ordenamos descendente para ver lo más reciente primero.
        return AccionAuditoria.objects.select_related('usuario').order_by('-fecha')

class TeacherAuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AccionAuditoria
    template_name = "docentes/audit_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def test_func(self):
        return self.request.user.es_docente()

    def get_queryset(self):
        # 1. Obtener las salas del docente
        salas = self.request.user.salas_asignadas.all()
        
        # 2. Obtener los IDs de alumnos de esas salas
        alumnos_ids = Alumno.objects.filter(sala__in=salas).values_list('id', flat=True)
        
        # 3. Obtener los IDs de asistencias de esos alumnos
        asistencias_ids = Asistencia.objects.filter(alumno__id__in=alumnos_ids).values_list('id', flat=True)

        # 4. Filtrar el log
        from django.db.models import Q
        return AccionAuditoria.objects.filter(
            (Q(modelo="Alumno") & Q(objeto_id__in=list(alumnos_ids))) |
            (Q(modelo="Asistencia") & Q(objeto_id__in=list(asistencias_ids)))
        ).select_related('usuario')


# =========================================================
# 📊 EXPORTACIÓN DE DATOS - COORDINADOR
# =========================================================

@login_required
@solo_coordinador
def exportar_docentes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="docentes.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Apellido', 'Nombre', 'DNI', 'Email', 'Teléfono', 'Estado'])

    docentes = Usuario.objects.filter(rol='docente').order_by('last_name', 'first_name')
    for doc in docentes:
        writer.writerow([doc.last_name, doc.first_name, doc.dni, doc.email, doc.telefono, 'Activo' if doc.is_active else 'Inactivo'])
    return response

@login_required
@solo_coordinador
def imprimir_docentes(request):
    docentes = Usuario.objects.filter(rol='docente').order_by('last_name', 'first_name')
    return render(request, "users/imprimir_docentes.html", {
        "docentes": docentes,
        "fecha": date.today()
    })

@login_required
@solo_coordinador
def exportar_salas_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salas.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nombre', 'Turno', 'Horario', 'Jardín', 'Docentes'])

    salas = Sala.objects.all().select_related('jardin').prefetch_related('docentes').order_by('jardin__nombre', 'nombre')
    for sala in salas:
        horario = f"{sala.horario_inicio.strftime('%H:%M')} a {sala.horario_fin.strftime('%H:%M')}"
        docentes = " - ".join([f"{d.last_name}, {d.first_name}" for d in sala.docentes.all()])
        writer.writerow([sala.nombre, sala.get_turno_display(), horario, sala.jardin.nombre, docentes])
    return response

@login_required
@solo_coordinador
def imprimir_salas(request):
    salas = Sala.objects.all().select_related('jardin').prefetch_related('docentes').order_by('jardin__nombre', 'nombre')
    return render(request, "users/imprimir_salas.html", {
        "salas": salas,
        "fecha": date.today()
    })

@login_required
@solo_coordinador
def exportar_espacios_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="espacios.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nombre', 'Dirección', 'Barrio', 'Sector', 'Programa', 'Subprograma'])

    jardines = Jardin.objects.all().select_related('programa', 'subprograma').order_by('nombre')
    for j in jardines:
        writer.writerow([j.nombre, j.direccion, j.barrio, j.sector, j.programa.nombre if j.programa else '-', j.subprograma.nombre if j.subprograma else '-'])
    return response

@login_required
@solo_coordinador
def imprimir_espacios(request):
    jardines = Jardin.objects.all().select_related('programa', 'subprograma').order_by('nombre')
    return render(request, "users/imprimir_espacios.html", {
        "jardines": jardines,
        "fecha": date.today()
    })

@login_required
@solo_coordinador
def exportar_programas_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="programas.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Nombre'])

    programas = Programa.objects.all().order_by('nombre')
    for p in programas:
        writer.writerow([p.id, p.nombre])
    return response

@login_required
@solo_coordinador
def imprimir_programas(request):
    programas = Programa.objects.all().order_by('nombre')
    return render(request, "users/imprimir_programas.html", {
        "programas": programas,
        "fecha": date.today()
    })

@login_required
@solo_coordinador
def exportar_subprogramas_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subprogramas.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Nombre', 'Programa'])

    subprogramas = Subprograma.objects.all().select_related('programa').order_by('programa__nombre', 'nombre')
    for s in subprogramas:
        writer.writerow([s.id, s.nombre, s.programa.nombre])
    return response

@login_required
@solo_coordinador
def imprimir_subprogramas(request):
    subprogramas = Subprograma.objects.all().select_related('programa').order_by('programa__nombre', 'nombre')
    return render(request, "users/imprimir_subprogramas.html", {
        "subprogramas": subprogramas,
        "fecha": date.today()
    })

@login_required
@solo_coordinador
def restablecer_password_docente(request, docente_id):
    docente = get_object_or_404(Usuario, id=docente_id, rol="docente")
    
    if request.method == "POST":
        form = RestablecerPasswordForm(request.POST)
        if form.is_valid():
            nueva_password = form.cleaned_data["password"]
            docente.set_password(nueva_password)
            docente.save()
            
            # Registrar en auditoría
            AccionAuditoria.objects.create(
                usuario=request.user,
                accion="modificacion",
                modelo="Usuario",
                objeto_id=docente.id,
                descripcion=f"Restablecimiento de contraseña para el docente {docente.username}"
            )
            
            return redirect("users:lista_docentes")
    else:
        form = RestablecerPasswordForm()
        
    return render(request, "users/restablecer_password.html", {"form": form, "docente": docente})

# =====================================================
# ELIMINACIÓN DE ENTIDADES
# =====================================================

@login_required
@solo_coordinador
def eliminar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.method == "POST":
        try:
            sala.delete()
            messages.success(request, f"La sala '{sala.nombre}' fue eliminada correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar la sala porque tiene alumnos o datos vinculados.")
    return redirect("users:lista_salas")

@login_required
@solo_coordinador
def eliminar_jardin(request, jardin_id):
    jardin = get_object_or_404(Jardin, id=jardin_id)
    if request.method == "POST":
        try:
            jardin.delete()
            messages.success(request, f"El espacio '{jardin.nombre}' fue eliminado correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar el espacio porque tiene salas asignadas.")
    return redirect("users:lista_espacios")

@login_required
@solo_coordinador
def eliminar_subprograma(request, subprograma_id):
    subprograma = get_object_or_404(Subprograma, id=subprograma_id)
    if request.method == "POST":
        try:
            subprograma.delete()
            messages.success(request, f"El subprograma '{subprograma.nombre}' fue eliminado correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar el subprograma porque tiene espacios asignados.")
    return redirect("users:lista_subprogramas")

@login_required
@solo_coordinador
def eliminar_docente(request, docente_id):
    docente = get_object_or_404(Usuario, id=docente_id, rol="docente")
    if request.method == "POST":
        try:
            docente.delete()
            messages.success(request, f"El docente {docente.username} fue eliminado correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar este docente porque tiene datos operativos vinculados.")
    return redirect("users:lista_docentes")
