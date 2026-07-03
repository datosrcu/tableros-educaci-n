import csv
import calendar
from datetime import date, datetime, timedelta
from django.utils import timezone

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import ProtectedError, Count, Q, Case, When, IntegerField

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

from jardines.models import Jardin, Programa, Subprograma, Sala, AsignacionDocenteSala
from alumnos.models import Alumno, Asistencia
from users.models import Usuario, AccionAuditoria


# =====================================================
# DASHBOARD COORDINADOR
# =====================================================

@login_required
@solo_coordinador
def dashboard_coordinador(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        espacios_count = Jardin.objects.count()
        programas_count = Programa.objects.count()
        subprogramas_count = Subprograma.objects.count()
        salas_count = Sala.objects.count()
        docentes_count = Usuario.objects.filter(rol="docente").count()
    else:
        programas = user.programas_asignados.all()
        espacios_count = Jardin.objects.filter(programa__in=programas).count()
        programas_count = programas.count()
        subprogramas_count = Subprograma.objects.filter(programa__in=programas).count()
        salas_count = Sala.objects.filter(jardin__programa__in=programas).count()
        docentes_count = Usuario.objects.filter(
            rol="docente",
            salas_asignadas__jardin__programa__in=programas
        ).distinct().count()

    context = {
        "espacios_count": espacios_count,
        "programas_count": programas_count,
        "subprogramas_count": subprogramas_count,
        "salas_count": salas_count,
        "docentes_count": docentes_count,
    }
    return render(request, "users/dashboard_coordinador.html", context)


# =====================================================
# LISTADOS
# =====================================================

@login_required
@solo_coordinador
def lista_espacios(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        espacios = Jardin.objects.all()
    else:
        espacios = Jardin.objects.filter(programa__in=user.programas_asignados.all())
    return render(request, "users/lista_espacios.html", {"espacios": espacios})


@login_required
@solo_coordinador
def lista_programas(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        programas = Programa.objects.all()
    else:
        programas = user.programas_asignados.all()
    return render(request, "users/lista_programas.html", {"programas": programas})


@login_required
@solo_coordinador
def lista_subprogramas(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        subprogramas = Subprograma.objects.select_related("programa").all()
    else:
        subprogramas = Subprograma.objects.filter(programa__in=user.programas_asignados.all()).select_related("programa")
    return render(request, "users/lista_subprogramas.html", {"subprogramas": subprogramas})


@login_required
@solo_coordinador
def lista_salas(request):
    user = request.user
    q = request.GET.get("q", "").strip()
    
    if user.es_admin() or not user.programas_asignados.exists():
        salas = Sala.objects.select_related("jardin").prefetch_related("asignaciones_docentes__docente", "subprograma", "responsable").all()
    else:
        salas = Sala.objects.filter(
            jardin__programa__in=user.programas_asignados.all()
        ).select_related("jardin", "subprograma", "responsable").prefetch_related("asignaciones_docentes__docente")
        
    if q:
        salas = salas.filter(
            Q(nombre__icontains=q) |
            Q(jardin__nombre__icontains=q) |
            Q(subprograma__nombre__icontains=q) |
            Q(responsable__first_name__icontains=q) |
            Q(responsable__last_name__icontains=q) |
            Q(responsable__username__icontains=q)
        ).distinct()
        
    return render(request, "users/lista_salas.html", {"salas": salas, "q": q})


@login_required
@solo_coordinador
def lista_docentes(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        docentes = Usuario.objects.filter(rol="docente")
    else:
        programas = user.programas_asignados.all()
        docentes = Usuario.objects.filter(
            Q(rol="docente") &
            (Q(salas_asignadas__jardin__programa__in=programas) | Q(programas_asignados__in=programas) | Q(salas_asignadas__isnull=True))
        ).distinct()
        
    q = request.GET.get('q', '').strip()
    if q:
        docentes = docentes.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(dni__icontains=q)
        )
        
    return render(request, "users/lista_docentes.html", {"docentes": docentes, "q": q})



# =====================================================
# CREACIÓN
# =====================================================

@login_required
@solo_coordinador
def crear_jardin(request):
    if request.method == "POST":
        form = JardinForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:lista_espacios")
    else:
        form = JardinForm(user=request.user)

    return render(request, "users/espacios/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_jardin(request, jardin_id):
    jardin = get_object_or_404(Jardin, id=jardin_id)
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if jardin.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para editar este espacio.")

    # 🔒 Validación de propiedad
    if not request.user.es_admin() and jardin.programa not in request.user.programas_asignados.all():
        raise PermissionDenied("No tiene permiso para editar este espacio.")

    if request.method == "POST":
        form = JardinForm(request.POST, instance=jardin, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:lista_espacios")
    else:
        form = JardinForm(instance=jardin, user=request.user)

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
            programa = form.save()
            # 🔒 Asignar automáticamente el programa al coordinador que lo crea
            if not request.user.es_admin():
                request.user.programas_asignados.add(programa)
            return redirect("users:lista_programas")
    else:
        form = ProgramaForm()

    return render(request, "users/programas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_programa(request, programa_id):
    programa = get_object_or_404(Programa, id=programa_id)

    # 🔒 Validación de propiedad
    if not request.user.es_admin() and programa not in request.user.programas_asignados.all():
        raise PermissionDenied("No tiene permiso para editar este programa.")

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
        form = SubprogramaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:lista_subprogramas")
    else:
        form = SubprogramaForm(user=request.user)

    return render(request, "users/subprogramas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_subprograma(request, subprograma_id):
    subprograma = get_object_or_404(Subprograma, id=subprograma_id)
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if subprograma.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para editar este subprograma.")

    if request.method == "POST":
        form = SubprogramaForm(request.POST, instance=subprograma, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("users:lista_subprogramas")
    else:
        form = SubprogramaForm(instance=subprograma, user=request.user)
    return render(request, "users/subprogramas/editar.html", {"form": form, "subprograma": subprograma})



@login_required
@solo_coordinador
def crear_sala(request):
    if request.method == "POST":
        form = SalaForm(request.POST, user=request.user)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f"La sala '{sala.nombre}' fue creada correctamente.")
            return redirect("users:lista_salas")
    else:
        form = SalaForm(user=request.user)

    return render(request, "users/salas/crear.html", {"form": form})


@login_required
@solo_coordinador
def editar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if sala.jardin.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para editar esta sala.")

    if request.method == "POST":
        form = SalaForm(request.POST, instance=sala, user=request.user)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f"La sala '{sala.nombre}' fue modificada correctamente.")
            return redirect("users:lista_salas")
    else:
        form = SalaForm(instance=sala, user=request.user)
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

    # 🔒 Validación de propiedad para coordinadores
    if not request.user.es_admin():
        from django.db.models import Q
        permiso = Usuario.objects.filter(id=docente_id, rol="docente").filter(
            Q(salas_asignadas__jardin__programa__in=request.user.programas_asignados.all()) |
            Q(salas_asignadas__isnull=True)
        ).exists()
        if not permiso:
            raise PermissionDenied("No tiene permiso para editar este docente.")

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
    user = request.user

    # 🔒 Validación de permisos
    if not user.es_admin() and user.programas_asignados.exists():
        if sala.jardin.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para asignar docentes en esta sala.")

    # 🔒 Validación de propiedad
    if not request.user.es_admin() and sala.jardin.programa not in request.user.programas_asignados.all():
        raise PermissionDenied("No tiene permiso para gestionar esta sala.")

    # Obtener docentes asignados a esta sala
    docentes_asignados = sala.docentes.all().order_by("last_name", "first_name")
    
    # Obtener asignaciones actuales (con días)
    asignaciones = sala.asignaciones_docentes.select_related("docente")
    docentes_asignados_dict = {a.docente_id: a for a in asignaciones}

    if request.method == "POST":
        # Crear o actualizar las asignaciones marcadas
        for docente in docentes_asignados:
            lunes = request.POST.get(f"lunes_{docente.id}") == "on"
            martes = request.POST.get(f"martes_{docente.id}") == "on"
            miercoles = request.POST.get(f"miercoles_{docente.id}") == "on"
            jueves = request.POST.get(f"jueves_{docente.id}") == "on"
            viernes = request.POST.get(f"viernes_{docente.id}") == "on"
            sabado = request.POST.get(f"sabado_{docente.id}") == "on"
            domingo = request.POST.get(f"domingo_{docente.id}") == "on"

            AsignacionDocenteSala.objects.update_or_create(
                sala=sala,
                docente=docente,
                defaults={
                    "lunes": lunes,
                    "martes": martes,
                    "miercoles": miercoles,
                    "jueves": jueves,
                    "viernes": viernes,
                    "sabado": sabado,
                    "domingo": domingo,
                }
            )

        # Registrar acción en auditoría
        nombres = ", ".join([f"{u.first_name} {u.last_name}" for u in docentes_asignados])
        desc = f"Docentes asignados a la sala '{sala.nombre}': [{nombres}] con días específicos."
        AccionAuditoria.objects.create(
            usuario=request.user,
            accion="asignacion",
            modelo="Sala",
            objeto_id=sala.id,
            descripcion=desc
        )

        messages.success(request, f"Las asignaciones de docentes para la sala '{sala.nombre}' fueron actualizadas.")
        return redirect("users:lista_salas")

    # Preparar datos para el listado en la plantilla (solo los docentes de la sala)
    docente_list = []
    for docente in docentes_asignados:
        asignacion = docentes_asignados_dict.get(docente.id)
        docente_list.append({
            'docente': docente,
            'asignado': True,
            'lunes': asignacion.lunes if asignacion else True,
            'martes': asignacion.martes if asignacion else True,
            'miercoles': asignacion.miercoles if asignacion else True,
            'jueves': asignacion.jueves if asignacion else True,
            'viernes': asignacion.viernes if asignacion else True,
            'sabado': asignacion.sabado if asignacion else False,
            'domingo': asignacion.domingo if asignacion else False,
        })

    return render(
        request,
        "users/asignar_docentes_sala.html",
        {
            "sala": sala,
            "docente_list": docente_list,
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
        from django.db.models import Q
        qs = AccionAuditoria.objects.select_related('usuario')
        usuario_id = self.request.GET.get('usuario')
        fecha = self.request.GET.get('fecha')
        search_query = self.request.GET.get('q')
        
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if fecha:
            try:
                qs = qs.filter(fecha__date=fecha)
            except (ValueError, TypeError):
                pass
        if search_query:
            qs = qs.filter(
                Q(usuario__username__icontains=search_query) |
                Q(usuario__first_name__icontains=search_query) |
                Q(usuario__last_name__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(modelo__icontains=search_query)
            )
            
        return qs.order_by('-fecha')


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
@login_required
@solo_coordinador
def exportar_docentes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="docentes.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Apellido', 'Nombre', 'DNI', 'Email', 'Teléfono', 'Estado'])

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        docentes = Usuario.objects.filter(rol='docente').order_by('last_name', 'first_name')
    else:
        programas = user.programas_asignados.all()
        docentes = Usuario.objects.filter(
            Q(rol="docente") &
            (Q(salas_asignadas__jardin__programa__in=programas) | Q(salas_asignadas__isnull=True))
        ).distinct().order_by('last_name', 'first_name')

    for doc in docentes:
        writer.writerow([doc.last_name, doc.first_name, doc.dni, doc.email, doc.telefono, 'Activo' if doc.is_active else 'Inactivo'])
    return response

@login_required
@solo_coordinador
def imprimir_docentes(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        docentes = Usuario.objects.filter(rol='docente').order_by('last_name', 'first_name')
    else:
        programas = user.programas_asignados.all()
        docentes = Usuario.objects.filter(
            Q(rol="docente") &
            (Q(salas_asignadas__jardin__programa__in=programas) | Q(salas_asignadas__isnull=True))
        ).distinct().order_by('last_name', 'first_name')
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

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        salas = Sala.objects.all().select_related('jardin').prefetch_related('asignaciones_docentes__docente').order_by('jardin__nombre', 'nombre')
    else:
        salas = Sala.objects.filter(jardin__programa__in=user.programas_asignados.all()).select_related('jardin').prefetch_related('asignaciones_docentes__docente').order_by('jardin__nombre', 'nombre')

    for sala in salas:
        horario = f"{sala.horario_inicio.strftime('%H:%M')} a {sala.horario_fin.strftime('%H:%M')}"
        
        docentes_list = []
        for asignacion in sala.asignaciones_docentes.all():
            d = asignacion.docente
            dias = []
            if asignacion.lunes: dias.append("L")
            if asignacion.martes: dias.append("M")
            if asignacion.miercoles: dias.append("M")
            if asignacion.jueves: dias.append("J")
            if asignacion.viernes: dias.append("V")
            if asignacion.sabado: dias.append("S")
            if asignacion.domingo: dias.append("D")
            dias_str = "".join(dias)
            docentes_list.append(f"{d.last_name}, {d.first_name} ({dias_str})")
        docentes = " - ".join(docentes_list)
        
        writer.writerow([sala.nombre, sala.get_turno_display(), horario, sala.jardin.nombre, docentes])
    return response

@login_required
@solo_coordinador
def imprimir_salas(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        salas = Sala.objects.all().select_related('jardin').prefetch_related('asignaciones_docentes__docente').order_by('jardin__nombre', 'nombre')
    else:
        salas = Sala.objects.filter(jardin__programa__in=user.programas_asignados.all()).select_related('jardin').prefetch_related('asignaciones_docentes__docente').order_by('jardin__nombre', 'nombre')
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
    writer.writerow(['Nombre', 'Dirección', 'Coordenadas', 'Sector', 'Programa', 'Subprograma'])

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        jardines = Jardin.objects.all().select_related('programa', 'subprograma').order_by('nombre')
    else:
        jardines = Jardin.objects.filter(programa__in=user.programas_asignados.all()).select_related('programa', 'subprograma').order_by('nombre')
    for j in jardines:
        writer.writerow([j.nombre, j.direccion, j.coordenadas, j.sector, j.programa.nombre if j.programa else '-', j.subprograma.nombre if j.subprograma else '-'])
    return response

@login_required
@solo_coordinador
def imprimir_espacios(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        jardines = Jardin.objects.all().select_related('programa', 'subprograma').order_by('nombre')
    else:
        jardines = Jardin.objects.filter(programa__in=user.programas_asignados.all()).select_related('programa', 'subprograma').order_by('nombre')
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

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        programas = Programa.objects.all().order_by('nombre')
    else:
        programas = user.programas_asignados.all().order_by('nombre')
    for p in programas:
        writer.writerow([p.id, p.nombre])
    return response

@login_required
@solo_coordinador
def imprimir_programas(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        programas = Programa.objects.all().order_by('nombre')
    else:
        programas = user.programas_asignados.all().order_by('nombre')
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

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        subprogramas = Subprograma.objects.all().select_related('programa').order_by('programa__nombre', 'nombre')
    else:
        subprogramas = Subprograma.objects.filter(programa__in=user.programas_asignados.all()).select_related('programa').order_by('programa__nombre', 'nombre')
    for s in subprogramas:
        writer.writerow([s.id, s.nombre, s.programa.nombre])
    return response

@login_required
@solo_coordinador
def imprimir_subprogramas(request):
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        subprogramas = Subprograma.objects.all().select_related('programa').order_by('programa__nombre', 'nombre')
    else:
        subprogramas = Subprograma.objects.filter(programa__in=user.programas_asignados.all()).select_related('programa').order_by('programa__nombre', 'nombre')
    return render(request, "users/imprimir_subprogramas.html", {
        "subprogramas": subprogramas,
        "fecha": date.today()
    })


@login_required
@solo_coordinador
def restablecer_password_docente(request, docente_id):
    docente = get_object_or_404(Usuario, id=docente_id, rol="docente")
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        # Validar si el docente pertenece a algún programa del coordinador o no tiene asignación
        en_jurisdiccion = docente.salas_asignadas.filter(jardin__programa__in=user.programas_asignados.all()).exists()
        sin_asignacion = docente.salas_asignadas.count() == 0
        if not (en_jurisdiccion or sin_asignacion):
            raise PermissionDenied("No tiene permiso para restablecer la contraseña de este docente.")
    
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
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if sala.jardin.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para eliminar esta sala.")
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
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if jardin.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para eliminar este espacio.")
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
    user = request.user

    if not user.es_admin() and user.programas_asignados.exists():
        if subprograma.programa not in user.programas_asignados.all():
            raise PermissionDenied("No tiene permiso para eliminar este subprograma.")
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

    # 🔒 Validación de propiedad
    if not request.user.es_admin():
        from django.db.models import Q
        permiso = Usuario.objects.filter(id=docente_id, rol="docente").filter(
            Q(salas_asignadas__jardin__programa__in=request.user.programas_asignados.all()) |
            Q(salas_asignadas__isnull=True)
        ).exists()
        if not permiso:
            raise PermissionDenied("No tiene permiso para eliminar este docente.")

    if request.method == "POST":
        try:
            docente.delete()
            messages.success(request, f"El docente {docente.username} fue eliminado correctamente.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar este docente porque tiene datos operativos vinculados.")
    return redirect("users:lista_docentes")


# =====================================================
# 📊 REPORTES DE ASISTENCIA (COORDINACIÓN)
# =====================================================

@login_required
@solo_coordinador
def reporte_asistencia_diaria(request):
    """
    Muestra qué jardines han tomado asistencia en una fecha específica.
    """
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_consulta = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_consulta = timezone.localdate()
    else:
        fecha_consulta = timezone.localdate()

    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        jardines = Jardin.objects.all().order_by('nombre')
    else:
        jardines = Jardin.objects.filter(programa__in=user.programas_asignados.all()).order_by('nombre')
    
    # Jardines con asistencia hoy
    jardines_con_asistencia_ids = Asistencia.objects.filter(
        fecha=fecha_consulta
    ).values_list('sala__jardin_id', flat=True).distinct()
    
    jardines_con = []
    jardines_sin = []
    
    for j in jardines:
        if j.id in jardines_con_asistencia_ids:
            jardines_con.append(j)
        else:
            jardines_sin.append(j)
            
    context = {
        'fecha': fecha_consulta,
        'jardines_con': jardines_con,
        'jardines_sin': jardines_sin,
        'total_con': len(jardines_con),
        'total_sin': len(jardines_sin),
    }
    return render(request, "users/reporte_asistencia_diaria.html", context)


@login_required
@solo_coordinador
def reporte_asistencia_mensual(request):
    """
    Genera la matriz de asistencia mensual por jardín.
    """
    ahora = timezone.localdate()
    mes = int(request.GET.get('mes', ahora.month))
    anio = int(request.GET.get('anio', ahora.year))
    
    # Obtener rango de días del mes
    primer_dia = date(anio, mes, 1)
    ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
    dias_mes = [date(anio, mes, d) for d in range(1, ultimo_dia_mes + 1)]
    
    user = request.user
    programa_id = request.GET.get('programa')
    
    if user.es_admin() or not user.programas_asignados.exists():
        programas = Programa.objects.all().order_by('nombre')
        if programa_id:
            jardines = Jardin.objects.filter(programa_id=programa_id)
        else:
            jardines = Jardin.objects.all()
    else:
        programas = user.programas_asignados.all().order_by('nombre')
        if programa_id:
            jardines = Jardin.objects.filter(programa__in=programas, programa_id=programa_id)
        else:
            jardines = Jardin.objects.filter(programa__in=programas)
            
    jardines = jardines.order_by('nombre')

    programa_seleccionado = None
    if programa_id:
        try:
            programa_seleccionado = next((p for p in programas if p.id == int(programa_id)), None)
        except (ValueError, TypeError):
            pass
    
    # Data para la matriz de presencias efectivas (excluye ausencias 'A')
    # { jardin_id: { dia: count } }
    asistencias = Asistencia.objects.filter(
        fecha__year=anio,
        fecha__month=mes,
        estado__in=['P', 'T', 'R', 'J']
    ).values('sala__jardin_id', 'fecha').annotate(count=Count('id'))
    
    data_asistencia = {}
    for a in asistencias:
        jid = a['sala__jardin_id']
        fecha = a['fecha']
        if jid not in data_asistencia:
            data_asistencia[jid] = {}
        data_asistencia[jid][fecha.day] = a['count']
        
    # Construir filas para el template
    filas = []
    totales_diarios = [0] * ultimo_dia_mes
    total_general_alumnos = 0
    
    for j in jardines:
        celdas = []
        dias_con_asistencia = 0
        total_alumnos_jardin = 0
        for d in range(1, ultimo_dia_mes + 1):
            valor = data_asistencia.get(j.id, {}).get(d, 0)
            celdas.append(valor)
            if valor > 0:
                dias_con_asistencia += 1
                totales_diarios[d-1] += valor
                total_alumnos_jardin += valor
        
        total_general_alumnos += total_alumnos_jardin
        filas.append({
            'jardin': j,
            'celdas': celdas,
            'total_dias': dias_con_asistencia,
            'total_alumnos_mes': total_alumnos_jardin
        })
        
    context = {
        'mes_nombre': calendar.month_name[mes].capitalize(),
        'mes': mes,
        'anio': anio,
        'dias_mes': range(1, ultimo_dia_mes + 1),
        'filas': filas,
        'totales_diarios': totales_diarios,
        'total_general_alumnos': total_general_alumnos,
        'anios_rango': range(ahora.year - 2, ahora.year + 1),
        'meses_rango': range(1, 13),
        'programas': programas,
        'programa_seleccionado': programa_seleccionado,
    }
    
    if 'export' in request.GET:
        return exportar_asistencia_mensual_csv(context)
    
    if 'print' in request.GET:
        return render(request, "users/imprimir_asistencia_mensual.html", context)

    return render(request, "users/reporte_asistencia_mensual.html", context)


def exportar_asistencia_mensual_csv(context):
    """
    Exporta la matriz mensual a CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="asistencia_mensual_{context["mes"]}_{context["anio"]}.csv"'
    
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    
    # Header con "Días"
    header = ['Jardin / Espacio'] + [f'Día {d}' for d in context['dias_mes']] + ['Días Cubiertos', 'Total Alumnos Mes']
    writer.writerow(header)
    
    for fila in context['filas']:
        row = [fila['jardin'].nombre] + [str(c) if c > 0 else '0' for c in fila['celdas']] + [str(fila['total_dias']), str(fila['total_alumnos_mes'])]
        writer.writerow(row)
    
    # Fila de Totales Diarios
    footer = ['TOTAL ALUMNOS POR DIA'] + [str(t) for t in context['totales_diarios']] + ['-', str(context['total_general_alumnos'])]
    writer.writerow(footer)
        
    return response
