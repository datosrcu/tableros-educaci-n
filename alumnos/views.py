"""
Vistas para la gestión de alumnos, asistencias y dashboard docente.
Este módulo contiene la lógica de negocio para la carga de datos de alumnos,
el registro de asistencia diaria y la exportación de reportes.
"""
import csv
import calendar
from datetime import date, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count

from .models import Alumno, Asistencia, MotivoJustificacion, FichaProgramaAlumno, AsignacionSala
from .forms import (
    AlumnoForm,
    FichaProgramaAlumnoForm,
    InscripcionForm,
)

from formularios.models import EstructuraFormulario, RespuestaFormulario
from formularios.forms import FormularioDinamico

from jardines.models import Sala
from users.decorators import rol_requerido
from users.models import AccionAuditoria


# =========================================================
# 🔐 UTILIDADES DE SEGURIDAD
# =========================================================

def docente_tiene_sala(user, sala_id):
    """Verifica si un docente tiene permiso (asignación) sobre una sala específica."""
    return user.salas_asignadas.filter(id=sala_id).exists()


def validar_alumno_para_docente(user, alumno):
    """
    Lanza PermissionDenied si el docente intenta acceder a un alumno
    que no pertenece a ninguna de sus salas asignadas.
    """
    if not AsignacionSala.objects.filter(alumno=alumno, sala__in=user.salas_asignadas.all()).exists():
        raise PermissionDenied


# =========================================================
# 🟨 DASHBOARD DOCENTE
# =========================================================

@login_required
@rol_requerido("docente")
def dashboard_docente(request):
    """
    Vista principal para el rol Docente. 
    Muestra el listado de salas que tiene bajo su responsabilidad.
    """
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
    """
    Muestra el listado de alumnos filtrado por rol:
    - Admin/Coordinador: Ven todos los alumnos.
    - Docente: Solo ve los alumnos de sus salas asignadas.
    """
    user = request.user

    # 🏢 Administradores y coordinadores ven todo el padrón
    if user.is_superuser or user.rol in ["administrador", "coordinador"]:
        alumnos = Alumno.objects.prefetch_related(
            "asignaciones",
            "asignaciones__sala__jardin"
        ).distinct()

    # 👨‍🏫 Docentes ven solo su jurisdicción
    elif user.rol == "docente":
        alumnos = Alumno.objects.filter(
            asignaciones__sala__in=user.salas_asignadas.all()
        ).prefetch_related(
            "asignaciones",
            "asignaciones__sala__jardin"
        ).distinct()

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
@rol_requerido("docente", "coordinador", "administrador")
def alumnos_por_sala(request, sala_id):
    """
    Lista los alumnos de una sala específica para que el docente
    pueda ver el listado o gestionar bajas (soft-delete).
    Los coordinadores solo visualizarán el listado base.
    """
    sala = get_object_or_404(Sala, id=sala_id)

    if request.user.rol == "docente" and not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    asignaciones = AsignacionSala.objects.filter(sala=sala).select_related('alumno')

    # 🔹 Acciones masivas de baja/activación
    if request.method == "POST" and request.user.rol == "docente":
        for asignacion in asignaciones:
            activo = request.POST.get(f'activo_{asignacion.alumno.id}') == "on"

            if asignacion.activo != activo:
                asignacion.activo = activo
                asignacion.fecha_baja = None if activo else date.today()
                
                if not activo:
                    asignacion.motivo_baja = request.POST.get(f'motivo_baja_{asignacion.alumno.id}', '').strip()
                else:
                    asignacion.motivo_baja = ''
                    
                asignacion.save()
                
                # Registrar en auditoría la baja
                if not activo:
                    AccionAuditoria.objects.create(
                        usuario=request.user,
                        accion="modificacion",
                        modelo="Alumno",
                        objeto_id=asignacion.alumno.id,
                        descripcion=f"El docente {request.user.username} dio de baja al alumno {asignacion.alumno.nombre} {asignacion.alumno.apellido} en la sala {sala.nombre}."
                    )

        return redirect("alumnos:alumnos_por_sala", sala_id=sala.id)

    return render(request, "docentes/alumnos_por_sala.html", {
        "sala": sala,
        "asignaciones": asignaciones
    })


# =========================================================
# ➕ AGREGAR ALUMNO (Formulario Mixto: Fijo + Dinámico)
# =========================================================

@login_required
@rol_requerido("docente")
def agregar_alumno(request, sala_id):
    """
    Alta de un nuevo alumno en una sala.
    Integra tres formularios:
    1. AlumnoForm (Datos básicos de Django)
    2. FichaProgramaAlumnoForm (Datos del Programa)
    3. FormularioDinamico (Campos variables definidos en DB)
    """
    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    # --- Lógica de Formulario Dinámico ---
    # Según el programa del jardín, buscamos si hay campos personalizados
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
        dni = request.POST.get('dni')
        if dni:
            dni = dni.strip()
        alumno_existente = Alumno.objects.filter(dni=dni).first() if dni else None

        if alumno_existente:
            # Solo vinculamos al alumno sin validar o sobreescribir los otros formularios
            # para asegurarnos que sus datos no se "pisen".
            asignacion, created = AsignacionSala.objects.get_or_create(
                alumno=alumno_existente, 
                sala=sala,
                defaults={'activo': True, 'fecha_baja': None}
            )
            # if they were already assigned but inactive, re-activate them:
            if not created and not asignacion.activo:
                asignacion.activo = True
                asignacion.fecha_baja = None
                asignacion.save()

            from django.contrib import messages
            messages.success(request, f"El alumno {alumno_existente.nombre} {alumno_existente.apellido} ya existía y fue asignado a la sala sin sobreescribir sus datos originales.")
            return redirect("alumnos:alumnos_por_sala", sala_id=sala.id)

        else:
            alumno_form = AlumnoForm(request.POST)
            ficha_form = FichaProgramaAlumnoForm(request.POST)

            # Validamos la tríada de formularios
            forms_valid = alumno_form.is_valid() and ficha_form.is_valid()
            if dynamic_form:
                forms_valid = forms_valid and dynamic_form.is_valid()

            if forms_valid:
                # 💾 1. Guardar Alumno
                alumno = alumno_form.save()
                asignacion, created = AsignacionSala.objects.get_or_create(
                    alumno=alumno, 
                    sala=sala,
                    defaults={'activo': True, 'fecha_baja': None}
                )

                # 💾 2. Guardar Ficha (datos extra)
                ficha = ficha_form.save(commit=False)
                ficha.alumno = alumno
                ficha.save()

                # 💾 3. Guardar respuesta dinámica si aplica
                if dynamic_form:
                    RespuestaFormulario.objects.create(
                        alumno=alumno,
                        formulario=estructura,
                        datos=dynamic_form.cleaned_data
                    )

                from django.contrib import messages
                messages.success(request, f"Alumno {alumno.nombre} {alumno.apellido} registrado correctamente.")

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
    """
    Edición de datos de un alumno. Mantiene la misma lógica 
    tripartita de formularios (Básico + Programa + Dinámico).
    """
    alumno = get_object_or_404(Alumno, id=alumno_id)
    validar_alumno_para_docente(request.user, alumno)

    # Obtenemos o creamos la ficha de datos extra
    ficha, _ = FichaProgramaAlumno.objects.get_or_create(alumno=alumno)

    # Determinamos si usa formulario ampliado según el programa/subprograma
    primera_asignacion = AsignacionSala.objects.filter(alumno=alumno).first()
    usa_ampliado = False
    if primera_asignacion:
        jardin = primera_asignacion.sala.jardin
        if jardin.subprograma:
            usa_ampliado = jardin.subprograma.usa_formulario_ampliado
        elif jardin.programa:
            usa_ampliado = jardin.programa.usa_formulario_ampliado

    programa = primera_asignacion.sala.jardin.programa if primera_asignacion else None
    estructura = getattr(programa, 'estructura_formulario', None) if programa else None
    dynamic_form = None
    respuesta_obj = None

    # Solo mostramos el formulario dinámico si usa ampliado
    if estructura and estructura.activo and usa_ampliado:
        # Buscamos si ya tiene respuestas previas para cargar el formulario
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
        ficha_form = FichaProgramaAlumnoForm(request.POST, instance=ficha) if usa_ampliado else None

        forms_valid = alumno_form.is_valid()
        if ficha_form:
            forms_valid = forms_valid and ficha_form.is_valid()
            
        if dynamic_form:
            forms_valid = forms_valid and dynamic_form.is_valid()

        if forms_valid:
            alumno_form.save()
            if ficha_form:
                ficha_form.save()

            # 💾 Actualizar/Crear respuesta dinámica
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

            return redirect("alumnos:detalle_alumno", alumno_id=alumno.id)

    else:
        alumno_form = AlumnoForm(instance=alumno)
        ficha_form = FichaProgramaAlumnoForm(instance=ficha) if usa_ampliado else None

    return render(request, "docentes/editar_alumno.html", {
        "alumno": alumno,
        "sala": primera_asignacion.sala if primera_asignacion else None,
        "alumno_form": alumno_form,
        "ficha_form": ficha_form,
        "dynamic_form": dynamic_form,
    })


# =========================================================
# 👁 DETALLE ALUMNO (Vista 360°)
# =========================================================

@login_required
@rol_requerido("docente", "coordinador", "administrador")
def detalle_alumno(request, alumno_id):
    """
    Vista detallada de un alumno:
    - Información personal y legajo.
    - Resumen estadístico de asistencias.
    - Listado histórico reciente.
    - Respuestas a formularios dinámicos.
    """
    alumno = get_object_or_404(Alumno, id=alumno_id)
    user = request.user

    if user.rol == "docente":
        validar_alumno_para_docente(user, alumno)

    # 📊 Filtrado y Cálculo de estadísticas
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    
    asistencias_base = Asistencia.objects.filter(alumno=alumno).select_related("motivo", "sala")
    
    # Resumen General (Histórico)
    resumen_qs = asistencias_base.order_by().values("estado").annotate(total=Count("id"))
    resumen_general = {r["estado"]: r["total"] for r in resumen_qs}

    if mes and anio:
        asistencias = asistencias_base.filter(fecha__month=mes, fecha__year=anio).order_by("-fecha")
        # Resumen Filtrado (Solo del mes seleccionado)
        resumen_f_qs = asistencias.order_by().values("estado").annotate(total=Count("id"))
        resumen_filtrado = {r["estado"]: r["total"] for r in resumen_f_qs}
        
        meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        periodo_label = f"Resumen de {meses_es[int(mes)]} {anio}"
    else:
        asistencias = asistencias_base.order_by("-fecha")
        resumen_filtrado = resumen_general
        periodo_label = "Resumen Histórico General"

    # Para el selector de fechas
    meses_rango = range(1, 13)
    anios_rango = range(date.today().year - 2, date.today().year + 1)
    
    # Cargamos datos dinámicos si existen
    respuesta_dinamica = RespuestaFormulario.objects.filter(alumno=alumno).first()

    return render(request, "alumnos/detalle_alumno.html", {
        "alumno": alumno,
        "asistencias": asistencias,
        "resumen": resumen_filtrado,
        "resumen_general": resumen_general,
        "periodo_label": periodo_label,
        "mes_sel": int(mes) if mes else None,
        "anio_sel": int(anio) if anio else None,
        "meses_rango": meses_rango,
        "anios_rango": anios_rango,
        "respuesta_dinamica": respuesta_dinamica,
    })


# =========================================================
# 📅 CARGAR ASISTENCIA (Carga Maestra Diaria)
# =========================================================

@login_required
@rol_requerido("docente")
def cargar_asistencia(request, sala_id):
    """
    Formulario maestro para cargar la asistencia de toda una sala en una fecha dada.
    Utiliza update_or_create para permitir correcciones sobre fechas pasadas.
    """
    sala = get_object_or_404(Sala, id=sala_id)

    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    # Determinar la fecha de carga (default hoy)
    fecha_str = request.GET.get("fecha") or request.POST.get("fecha")

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(asignaciones__sala=sala, asignaciones__activo=True)
    motivos = MotivoJustificacion.objects.all()

    if request.method == "POST":
        from django.contrib import messages
        try:
            for alumno in alumnos:
                estado = request.POST.get(f"estado_{alumno.id}", "P")
                motivo_id = request.POST.get(f"motivo_{alumno.id}")
                observaciones = request.POST.get(f"observaciones_{alumno.id}", "").strip()
                
                motivo = None
                if estado in ["J", "T", "R"] and motivo_id:
                    motivo = MotivoJustificacion.objects.filter(id=motivo_id).first()
                elif estado not in ["J", "T", "R"]:
                    motivo = None

                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    fecha=fecha,
                    sala=sala,
                    defaults={
                        "estado": estado,
                        "motivo": motivo,
                        "observaciones": observaciones,
                        "docente": request.user
                    }
                )
            messages.success(request, f"Asistencia del {fecha} guardada correctamente.")
            return redirect("alumnos:cargar_asistencia", sala_id=sala.id)
        except ValidationError as e:
            messages.error(request, f"Error al guardar: {e.message if hasattr(e, 'message') else e.messages[0]}")

    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos,
        fecha=fecha,
        sala=sala
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
@rol_requerido("docente", "coordinador", "administrador")
def ver_asistencias(request, sala_id):
    """Vista de solo lectura para revisar las asistencias de un día específico."""
    sala = get_object_or_404(Sala, id=sala_id)

    if request.user.rol == "docente" and not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(asignaciones__sala=sala, asignaciones__activo=True)

    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos,
        fecha=fecha,
        sala=sala
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
    """
    Formulario de pre-inscripción para nuevos alumnos. 
    Permite el ingreso inicial de datos antes de ser validados por un docente.
    """
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
@rol_requerido("docente", "coordinador", "administrador")
def crear_tutor_ajax(request):
    """
    Punto de entrada AJAX para crear tutores sobre la marcha 
    durante la carga de un alumno.
    """
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
    """Exporta el padrón activo de una sala a formato CSV compatible con Excel."""
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="alumnos_{sala.nombre}.csv"'
    
    # UTF-8 with BOM for Excel compatibility
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Apellido', 'Nombre', 'DNI', 'Fecha Nacimiento', 'Estado'])

    asignaciones = AsignacionSala.objects.filter(sala=sala).select_related('alumno')
    for a in asignaciones:
        writer.writerow([a.alumno.apellido, a.alumno.nombre, a.alumno.dni, a.alumno.fecha_nacimiento.strftime('%d/%m/%Y') if a.alumno.fecha_nacimiento else '-', 'Activo' if a.activo else 'Baja'])

    return response


@login_required
@rol_requerido("coordinador", "administrador")
def exportar_alumnos_completo_csv(request):
    """
    Exporta el padrón completo de alumnos de la base de datos 
    con información detallada (datos básicos + ficha programa).
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="padron_completo_alumnos_{date.today()}.csv"'
    
    # UTF-8 con BOM para compatibilidad con Excel
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    
    # Cabecera
    writer.writerow([
        'Apellido', 'Nombre', 'DNI', 'Fecha Nacimiento', 
        'Espacios/Salas', 'Estado General',
        'Nivel Educativo', 'Situación Laboral', 'Obra Social', 'Escolaridad', 'Teléfono'
    ])

    alumnos = Alumno.objects.prefetch_related(
        'asignaciones__sala__jardin',
        'ficha_programa'
    ).order_by('apellido', 'nombre')

    for alumno in alumnos:
        # Espacios y salas
        salas_info = []
        for asig in alumno.asignaciones.all():
            estado = "Activo" if asig.activo else "Baja"
            salas_info.append(f"{asig.sala.jardin.nombre} - {asig.sala.nombre} ({estado})")
        
        salas_str = " | ".join(salas_info) if salas_info else "Sin asignar"
        
        # Estado general
        tiene_activo = any(asig.activo for asig in alumno.asignaciones.all())
        estado_gen = "ACTIVO" if tiene_activo else ("BAJA" if alumno.asignaciones.exists() else "SIN ASIGNAR")
        
        # Ficha Programa
        ficha = getattr(alumno, 'ficha_programa', None)
        nivel = ficha.nivel_educativo if ficha else "-"
        situacion = ficha.situacion_laboral if ficha else "-"
        obra = ficha.obra_social if ficha else "-"
        escolaridad = ficha.escolaridad if ficha else "-"
        tel = ficha.telefono if ficha else "-"

        writer.writerow([
            alumno.apellido, 
            alumno.nombre, 
            alumno.dni, 
            alumno.fecha_nacimiento.strftime('%d/%m/%Y') if alumno.fecha_nacimiento else '-',
            salas_str,
            estado_gen,
            nivel,
            situacion,
            obra,
            escolaridad,
            tel
        ])

    return response


@login_required
@rol_requerido("docente")
def imprimir_alumnos_sala(request, sala_id):
    """Genera una vista HTML optimizada para imprimir el listado de alumnos."""
    sala = get_object_or_404(Sala, id=sala_id)
    if not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    asignaciones = AsignacionSala.objects.filter(sala=sala, activo=True).select_related('alumno').order_by('alumno__apellido')
    alumnos = [a.alumno for a in asignaciones]
    return render(request, "docentes/imprimir_alumnos.html", {
        "sala": sala,
        "alumnos": alumnos,
        "fecha": date.today()
    })


@login_required
@rol_requerido("docente", "coordinador", "administrador")
def exportar_asistencias_csv(request, sala_id):
    """Exporta el registro de asistencia del día a formato CSV."""
    sala = get_object_or_404(Sala, id=sala_id)
    if request.user.rol == "docente" and not docente_tiene_sala(request.user, sala.id):
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
        sala=sala,
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
@rol_requerido("docente", "coordinador", "administrador")
def imprimir_asistencias_sala(request, sala_id):
    """Genera una página HTML optimizada para imprimir el parte diario de asistencia."""
    sala = get_object_or_404(Sala, id=sala_id)
    if request.user.rol == "docente" and not docente_tiene_sala(request.user, sala.id):
        raise PermissionDenied

    fecha_str = request.GET.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        fecha = date.today()

    alumnos = Alumno.objects.filter(asignaciones__sala=sala, asignaciones__activo=True).order_by('apellido')
    asistencias = Asistencia.objects.filter(alumno__in=alumnos, fecha=fecha, sala=sala).select_related('motivo')
    asistencias_dict = {a.alumno_id: a for a in asistencias}

    return render(request, "docentes/imprimir_asistencias.html", {
        "sala": sala,
        "alumnos": alumnos,
        "asistencias_dict": asistencias_dict,
        "fecha": fecha,
    })
