import csv
from datetime import date, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count

from .models import Alumno, Asistencia, MotivoJustificacion, FichaProgramaAlumno
from .forms import (
    AlumnoForm,
    FichaProgramaAlumnoForm,
    InscripcionForm,
)

from formularios.models import EstructuraFormulario, RespuestaFormulario
from formularios.forms import FormularioDinamico

from jardines.models import Sala
from users.decorators import rol_requerido


# =========================================================
# 🔐 UTILIDADES DE SEGURIDAD
# =========================================================

def docente_tiene_sala(user, sala_id):
    return user.salas_asignadas.filter(id=sala_id).exists()


def validar_alumno_para_docente(user, alumno):
    if not docente_tiene_sala(user, alumno.sala_id):
        raise PermissionDenied


# =========================================================
# 🟨 DASHBOARD DOCENTE
# =========================================================

@login_required
@rol_requerido("docente")
def dashboard_docente(request):

    salas = (
        request.user.salas_asignadas
        .select_related(
            "jardin",
            "jardin__programa",
            "jardin__subprograma",
        )
        .all()
    )

    return render(request, "alumnos/dashboard_docente.html", {
        "salas": salas
    })


# =========================================================
# 📋 LISTA GENERAL DE ALUMNOS (por rol)
# =========================================================

@login_required
@rol_requerido("docente", "coordinador", "administrador")
def lista_alumnos(request):

    user = request.user

    if user.is_superuser or user.rol in ["administrador", "coordinador"]:
        alumnos = Alumno.objects.select_related(
            "sala",
            "sala__jardin"
        )

    elif user.rol == "docente":
        alumnos = Alumno.objects.filter(
            sala__in=user.salas_asignadas.all()
        ).select_related(
            "sala",
            "sala__jardin"
        )

    else:
        raise PermissionDenied

    return render(
        request,
        "alumnos/lista_alumnos.html",
        {"alumnos": alumnos}
    )


# =========================================================
# 👶 ALUMNOS POR SALA (DOCENTE)
# =========================================================

@login_required
@rol_requerido("docente")
def alumnos_por_sala(request, sala_id):

    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    alumnos = Alumno.objects.filter(
        sala=sala,
        activo=True
    )

    if request.method == "POST":
        for alumno in alumnos:
            activo = request.POST.get(f'activo_{alumno.id}') == "on"

            if alumno.activo != activo:
                alumno.activo = activo
                alumno.fecha_baja = None if activo else date.today()
                alumno.save()

        return redirect("alumnos:alumnos_por_sala", sala_id=sala.id)

    return render(request, "docentes/alumnos_por_sala.html", {
        "sala": sala,
        "alumnos": alumnos
    })


# =========================================================
# ➕ AGREGAR ALUMNO
# =========================================================

@login_required
@rol_requerido("docente")
def agregar_alumno(request, sala_id):

    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    # --- Lógica de Formulario Dinámico ---
    programa = sala.jardin.programa
    estructura = getattr(programa, 'estructura_formulario', None)
    dynamic_form = None

    if estructura and estructura.activo:
        if request.method == "POST":
            dynamic_form = FormularioDinamico(request.POST, estructura=estructura)
        else:
            dynamic_form = FormularioDinamico(estructura=estructura)
    # -------------------------------------

    if request.method == "POST":
        alumno_form = AlumnoForm(request.POST)
        ficha_form = FichaProgramaAlumnoForm(request.POST)

        # Validamos todos los formularios involucrados
        forms_valid = alumno_form.is_valid() and ficha_form.is_valid()
        if dynamic_form:
            forms_valid = forms_valid and dynamic_form.is_valid()

        if forms_valid:
            alumno = alumno_form.save(commit=False)
            alumno.sala = sala
            alumno.save()
            alumno_form.save_m2m()

            ficha = ficha_form.save(commit=False)
            ficha.alumno = alumno
            ficha.save()

            # Guardar respuesta dinámica si existe
            if dynamic_form:
                RespuestaFormulario.objects.create(
                    alumno=alumno,
                    formulario=estructura,
                    datos=dynamic_form.cleaned_data
                )

            return redirect("alumnos:alumnos_por_sala", sala_id=sala.id)

    else:
        alumno_form = AlumnoForm()
        ficha_form = FichaProgramaAlumnoForm()

    return render(request, "docentes/agregar_alumno.html", {
        "alumno_form": alumno_form,
        "ficha_form": ficha_form,
        "dynamic_form": dynamic_form,
        "sala": sala
    })


# =========================================================
# ✏ EDITAR ALUMNO
# =========================================================

@login_required
@rol_requerido("docente")
def editar_alumno(request, alumno_id):

    alumno = get_object_or_404(Alumno, id=alumno_id)

    validar_alumno_para_docente(request.user, alumno)

    ficha, _ = FichaProgramaAlumno.objects.get_or_create(alumno=alumno)

    # --- Lógica de Formulario Dinámico ---
    programa = alumno.sala.jardin.programa
    estructura = getattr(programa, 'estructura_formulario', None)
    dynamic_form = None
    respuesta_obj = None

    if estructura and estructura.activo:
        respuesta_obj = RespuestaFormulario.objects.filter(
            alumno=alumno, formulario=estructura
        ).first()
        initial_data = respuesta_obj.datos if respuesta_obj else {}

        if request.method == "POST":
            dynamic_form = FormularioDinamico(
                request.POST, estructura=estructura, initial=initial_data
            )
        else:
            dynamic_form = FormularioDinamico(
                estructura=estructura, initial=initial_data
            )
    # -------------------------------------

    if request.method == "POST":
        alumno_form = AlumnoForm(request.POST, instance=alumno)
        ficha_form = FichaProgramaAlumnoForm(request.POST, instance=ficha)

        # Validamos todos los formularios
        forms_valid = alumno_form.is_valid() and ficha_form.is_valid()
        if dynamic_form:
            forms_valid = forms_valid and dynamic_form.is_valid()

        if forms_valid:
            alumno_form.save()
            ficha_form.save()

            # Guardar/Actualizar respuesta dinámica
            if dynamic_form:
                if respuesta_obj:
                    respuesta_obj.datos = dynamic_form.cleaned_data
                    respuesta_obj.save()
                else:
                    RespuestaFormulario.objects.create(
                        alumno=alumno,
                        formulario=estructura,
                        datos=dynamic_form.cleaned_data
                    )

            return redirect(
                "alumnos:alumnos_por_sala",
                sala_id=alumno.sala.id
            )

    else:
        alumno_form = AlumnoForm(instance=alumno)
        ficha_form = FichaProgramaAlumnoForm(instance=ficha)

    return render(request, "docentes/editar_alumno.html", {
        "alumno": alumno,
        "sala": alumno.sala,
        "alumno_form": alumno_form,
        "ficha_form": ficha_form,
        "dynamic_form": dynamic_form,
    })


# =========================================================
# 👁 DETALLE ALUMNO
# =========================================================

@login_required
@rol_requerido("docente", "coordinador", "administrador")
def detalle_alumno(request, alumno_id):

    alumno = get_object_or_404(Alumno, id=alumno_id)
    user = request.user

    # 🔒 Seguridad docente
    if user.rol == "docente":
        validar_alumno_para_docente(user, alumno)

    asistencias = (
        Asistencia.objects
        .filter(alumno=alumno)
        .select_related("motivo")
        .order_by("-fecha")
    )

    resumen = asistencias.values("estado").annotate(total=Count("estado"))
    resumen_dict = {r["estado"]: r["total"] for r in resumen}

    # --- Lógica de Respuesta Dinámica ---
    respuesta_dinamica = RespuestaFormulario.objects.filter(alumno=alumno).first()

    return render(request, "alumnos/detalle_alumno.html", {
        "alumno": alumno,
        "asistencias": asistencias,
        "resumen": resumen_dict,
        "respuesta_dinamica": respuesta_dinamica,
    })


# =========================================================
# 📅 CARGAR ASISTENCIA
# =========================================================

@login_required
@rol_requerido("docente")
def cargar_asistencia(request, sala_id):

    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha") or request.POST.get("fecha")

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(sala=sala, activo=True)
    motivos = MotivoJustificacion.objects.all()

    if request.method == "POST":

        for alumno in alumnos:
            estado = request.POST.get(f"estado_{alumno.id}", "P")
            motivo_id = request.POST.get(f"motivo_{alumno.id}")
            
            motivo = None
            if estado == "J" and motivo_id:
                motivo = MotivoJustificacion.objects.filter(id=motivo_id).first()
            elif estado != "J":
                motivo = None

            Asistencia.objects.update_or_create(
                alumno=alumno,
                fecha=fecha,
                defaults={
                    "estado": estado,
                    "motivo": motivo,
                    "docente": request.user
                }
            )

        return redirect("alumnos:cargar_asistencia", sala_id=sala.id)

    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos,
        fecha=fecha
    ).select_related("motivo")

    asistencias_dict = {a.alumno_id: a for a in asistencias_existentes}
    
    asistencia_data = []
    for alumno in alumnos:
        asistencia_data.append({
            'alumno': alumno,
            'asistencia': asistencias_dict.get(alumno.id)
        })

    return render(request, "docentes/asistencia_form.html", {
        "sala": sala,
        "asistencia_data": asistencia_data,
        "fecha": fecha,
        "motivos": motivos
    })


# =========================================================
# 📋 VER HISTORIAL DE ASISTENCIAS
# =========================================================

@login_required
@rol_requerido("docente")
def ver_asistencias(request, sala_id):

    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(sala=sala, activo=True)

    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos,
        fecha=fecha
    ).select_related("motivo")

    asistencias_dict = {a.alumno_id: a for a in asistencias_existentes}

    return render(request, "docentes/ver_asistencias.html", {
        "sala": sala,
        "alumnos": alumnos,
        "asistencias_dict": asistencias_dict,
        "fecha": fecha,
    })


# =========================================================
# 🌍 INSCRIPCIÓN PÚBLICA
# =========================================================

@login_required
def inscripcion_participante(request):

    if request.method == "POST":
        form = InscripcionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inscripcion_ok")
    else:
        form = InscripcionForm()

    return render(request, "alumnos/inscripcion_form.html", {
        "form": form
    })


@login_required
def crear_tutor_ajax(request):
    if request.method == "POST":
        from .forms import TutorForm
        form = TutorForm(request.POST)
        if form.is_valid():
            tutor = form.save()
            return JsonResponse({
                "success": True,
                "id": tutor.id,
                "nombre": f"{tutor.apellido}, {tutor.nombre}"
            })
        else:
            error_msg = ""
            for field, errors in form.errors.items():
                error_msg += f"{field.capitalize()}: {', '.join(errors)}\n"
            return JsonResponse({"success": False, "errors": error_msg}, status=400)
    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)


# =========================================================
# 📊 EXPORTACIÓN DE DATOS
# =========================================================

@login_required
@rol_requerido("docente")
def exportar_alumnos_csv(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="alumnos_{sala.nombre}.csv"'
    
    # UTF-8 with BOM for Excel compatibility
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Apellido', 'Nombre', 'DNI', 'Fecha Nacimiento', 'Estado'])

    alumnos = Alumno.objects.filter(sala=sala)
    for a in alumnos:
        writer.writerow([a.apellido, a.nombre, a.dni, a.fecha_nacimiento.strftime('%d/%m/%Y') if a.fecha_nacimiento else '-', 'Activo' if a.activo else 'Baja'])

    return response


@login_required
@rol_requerido("docente")
def imprimir_alumnos_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    alumnos = Alumno.objects.filter(sala=sala, activo=True).order_by('apellido')
    return render(request, "docentes/imprimir_alumnos.html", {
        "sala": sala,
        "alumnos": alumnos,
        "fecha": date.today()
    })


@login_required
@rol_requerido("docente")
def exportar_asistencias_csv(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="asistencias_{sala.nombre}_{fecha}.csv"'
    
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Fecha', 'Alumno', 'DNI', 'Estado', 'Justificación'])

    asistencias = Asistencia.objects.filter(
        alumno__sala=sala,
        fecha=fecha
    ).select_related('alumno', 'motivo')

    for a in asistencias:
        writer.writerow([
            a.fecha.strftime('%d/%m/%Y'),
            f"{a.alumno.apellido}, {a.alumno.nombre}",
            a.alumno.dni,
            a.get_estado_display(),
            a.motivo.nombre if a.motivo else '-'
        ])

    return response


@login_required
@rol_requerido("docente")
def imprimir_asistencias_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(sala=sala, activo=True).order_by('apellido')
    asistencias = Asistencia.objects.filter(alumno__in=alumnos, fecha=fecha).select_related('motivo')
    asistencias_dict = {a.alumno_id: a for a in asistencias}

    return render(request, "docentes/imprimir_asistencias.html", {
        "sala": sala,
        "alumnos": alumnos,
        "asistencias_dict": asistencias_dict,
        "fecha": fecha,
    })
