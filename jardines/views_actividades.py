import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

from users.decorators import rol_requerido
from users.models import Usuario
from .models import ActividadEspecial, TipoActividadEspecial, Programa, Jardin, AsistenciaDocente
from .forms import ActividadEspecialForm, TipoActividadEspecialForm


def _sincronizar_asistencias_por_actividad(actividad):
    """
    Actualiza los registros de asistencia existentes no fichados de los docentes afectados
    en la fecha de la actividad para reflejar la exención ('E') considerando el turno afectado.
    """
    docentes_afectados = actividad.obtener_docentes_afectados()
    if not docentes_afectados.exists():
        return

    # Buscar registros no fichados de esos docentes en la fecha del evento
    asistencias = AsistenciaDocente.objects.filter(
        docente__in=docentes_afectados,
        fecha=actividad.fecha,
        fichado=False
    ).exclude(estado='L')

    for asist in asistencias:
        # Si la actividad solo afecta a un turno y este registro es de otro turno, no eximir
        if actividad.turno_afectado != 'todo_el_dia' and asist.turno and asist.turno != actividad.turno_afectado:
            continue

        # Verificar si la sala de la asistencia está exenta
        salas_docente = asist.docente.salas_asignadas.filter(jardin=asist.jardin)
        if asist.turno:
            salas_docente = salas_docente.filter(turno=asist.turno)

        sala = salas_docente.first()
        if sala and sala.horario_inicio and sala.horario_fin:
            # Si franja distinta
            if actividad.hora_fin <= sala.horario_inicio or actividad.hora_inicio >= sala.horario_fin:
                asist.estado = 'E'
                asist.observaciones = f"Exento de clase habitual por actividad especial: {actividad.nombre} ({actividad.hora_inicio.strftime('%H:%M')} a {actividad.hora_fin.strftime('%H:%M')} hs)."
                asist.save()
            elif actividad.hora_inicio > sala.horario_inicio and actividad.hora_fin >= sala.horario_fin:
                asist.observaciones = f"Clase habitual con solapamiento por actividad especial: {actividad.nombre} a las {actividad.hora_inicio.strftime('%H:%M')} hs (exención del tramo restante tras fichado de ingreso)."
                asist.save()
        else:
            asist.estado = 'E'
            asist.observaciones = f"Exento por actividad especial: {actividad.nombre} ({actividad.hora_inicio.strftime('%H:%M')} a {actividad.hora_fin.strftime('%H:%M')} hs)."
            asist.save()


@login_required
@rol_requerido("coordinador", "administrador")
def lista_actividades(request):
    user = request.user
    q = request.GET.get("q", "").strip()
    tipo_id = request.GET.get("tipo")
    alcance = request.GET.get("alcance")
    fecha_filtro = request.GET.get("fecha")

    if user.es_admin() or not user.programas_asignados.exists():
        actividades = ActividadEspecial.objects.select_related("tipo", "programa", "jardin", "creado_por").all()
    else:
        programas = user.programas_asignados.all()
        actividades = ActividadEspecial.objects.filter(
            Q(programa__in=programas) |
            Q(jardin__programa__in=programas) |
            Q(salas__jardin__programa__in=programas) |
            Q(docentes__salas_asignadas__jardin__programa__in=programas) |
            Q(creado_por=user)
        ).select_related("tipo", "programa", "jardin", "creado_por").distinct()

    if q:
        actividades = actividades.filter(
            Q(nombre__icontains=q) |
            Q(tipo__nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(jardin__nombre__icontains=q) |
            Q(programa__nombre__icontains=q)
        ).distinct()

    if tipo_id:
        actividades = actividades.filter(tipo_id=tipo_id)

    if alcance:
        actividades = actividades.filter(alcance=alcance)

    if fecha_filtro:
        actividades = actividades.filter(fecha=fecha_filtro)

    actividades = actividades.order_by("-fecha", "hora_inicio")

    # Contar docentes afectados para cada actividad
    for act in actividades:
        act.total_docentes = act.obtener_docentes_afectados().count()

    tipos = TipoActividadEspecial.objects.filter(activo=True).order_by("nombre")

    return render(request, "actividades/lista.html", {
        "actividades": actividades,
        "tipos": tipos,
        "q": q,
        "tipo_sel": tipo_id,
        "alcance_sel": alcance,
        "fecha_sel": fecha_filtro,
        "ALCANCE_CHOICES": ActividadEspecial.ALCANCE_CHOICES,
    })


@login_required
@rol_requerido("coordinador", "administrador")
def crear_actividad(request):
    form = ActividadEspecialForm(request.POST or None, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            act = form.save(commit=False)
            act.creado_por = request.user
            act.save()
            form.save_m2m()

            # Sincronizar asistencias del día si coincide con la fecha
            _sincronizar_asistencias_por_actividad(act)

            messages.success(request, f"Actividad especial '{act.nombre}' creada con éxito.")
            return redirect("jardines:lista_actividades")

    return render(request, "actividades/form.html", {
        "form": form,
        "titulo": "Registrar Actividad Especial",
    })


@login_required
@rol_requerido("coordinador", "administrador")
def editar_actividad(request, pk):
    act = get_object_or_404(ActividadEspecial, pk=pk)

    # Validar permisos de jurisdicción
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        pertenece = False
        if act.programa and act.programa in programas:
            pertenece = True
        elif act.jardin and act.jardin.programa in programas:
            pertenece = True
        elif act.salas.filter(jardin__programa__in=programas).exists():
            pertenece = True
        elif act.docentes.filter(salas_asignadas__jardin__programa__in=programas).exists():
            pertenece = True
        elif act.creado_por == request.user:
            pertenece = True

        if not pertenece:
            raise PermissionDenied("No tiene permiso para editar esta actividad.")

    form = ActividadEspecialForm(request.POST or None, instance=act, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            act = form.save()
            form.save_m2m()

            _sincronizar_asistencias_por_actividad(act)

            messages.success(request, f"Actividad especial '{act.nombre}' actualizada con éxito.")
            return redirect("jardines:lista_actividades")

    return render(request, "actividades/form.html", {
        "form": form,
        "actividad": act,
        "titulo": "Editar Actividad Especial",
    })


@login_required
@rol_requerido("coordinador", "administrador")
def eliminar_actividad(request, pk):
    act = get_object_or_404(ActividadEspecial, pk=pk)

    # Validar permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        pertenece = False
        if act.programa and act.programa in programas:
            pertenece = True
        elif act.jardin and act.jardin.programa in programas:
            pertenece = True
        elif act.salas.filter(jardin__programa__in=programas).exists():
            pertenece = True
        elif act.docentes.filter(salas_asignadas__jardin__programa__in=programas).exists():
            pertenece = True
        elif act.creado_por == request.user:
            pertenece = True

        if not pertenece:
            raise PermissionDenied("No tiene permiso para eliminar esta actividad.")

    if request.method == "POST":
        nombre = act.nombre
        fecha = act.fecha
        docentes_afectados = list(act.obtener_docentes_afectados())
        act.delete()

        # Revertir registros 'E' no fichados de docentes que ya no tienen otra actividad hoy
        for d in docentes_afectados:
            otras_act = ActividadEspecial.obtener_actividades_docente(d, fecha)
            if not otras_act.exists():
                AsistenciaDocente.objects.filter(
                    docente=d,
                    fecha=fecha,
                    fichado=False,
                    estado='E'
                ).update(
                    estado='A',
                    observaciones='Registro restablecido al eliminar actividad especial.'
                )

        messages.success(request, f"Actividad especial '{nombre}' eliminada correctamente.")
        return redirect("jardines:lista_actividades")

    return render(request, "actividades/eliminar_confirmar.html", {
        "actividad": act,
    })


@login_required
@rol_requerido("coordinador", "administrador")
def ver_detalle_actividad(request, pk):
    act = get_object_or_404(ActividadEspecial.objects.select_related("tipo", "programa", "jardin", "creado_por"), pk=pk)

    # Validar permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        pertenece = False
        if act.programa and act.programa in programas:
            pertenece = True
        elif act.jardin and act.jardin.programa in programas:
            pertenece = True
        elif act.salas.filter(jardin__programa__in=programas).exists():
            pertenece = True
        elif act.docentes.filter(salas_asignadas__jardin__programa__in=programas).exists():
            pertenece = True
        elif act.creado_por == request.user:
            pertenece = True

        if not pertenece:
            raise PermissionDenied("No tiene permiso para ver esta actividad.")

    docentes_afectados = act.obtener_docentes_afectados().order_by("last_name", "first_name")

    return render(request, "actividades/detalle.html", {
        "actividad": act,
        "docentes_afectados": docentes_afectados,
    })


@login_required
@rol_requerido("coordinador", "administrador")
def crear_tipo_actividad_ajax(request):
    """Endpoint AJAX para crear un nuevo TipoActividadEspecial sobre la marcha."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)

    nombre = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()

    if not nombre:
        return JsonResponse({"status": "error", "message": "El nombre del tipo de actividad es obligatorio."}, status=400)

    tipo, created = TipoActividadEspecial.objects.get_or_create(
        nombre=nombre,
        defaults={
            "descripcion": descripcion,
            "es_default": False,
            "activo": True
        }
    )

    return JsonResponse({
        "status": "success",
        "id": tipo.id,
        "nombre": tipo.nombre,
        "created": created
    })


@login_required
@rol_requerido("coordinador", "administrador")
def exportar_actividades_csv(request):
    """Exporta el listado de actividades especiales a CSV."""
    user = request.user
    if user.es_admin() or not user.programas_asignados.exists():
        actividades = ActividadEspecial.objects.select_related("tipo", "programa", "jardin").all()
    else:
        programas = user.programas_asignados.all()
        actividades = ActividadEspecial.objects.filter(
            Q(programa__in=programas) |
            Q(jardin__programa__in=programas) |
            Q(salas__jardin__programa__in=programas) |
            Q(docentes__salas_asignadas__jardin__programa__in=programas) |
            Q(creado_por=user)
        ).select_related("tipo", "programa", "jardin").distinct()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="actividades_especiales.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(["Nombre", "Tipo", "Fecha", "Hora Inicio", "Hora Fin", "Alcance", "Detalle Alcance", "Docentes Afectados"])

    for a in actividades.order_by("-fecha", "hora_inicio"):
        detalle_alcance = "—"
        if a.alcance == 'programa' and a.programa:
            detalle_alcance = a.programa.nombre
        elif a.alcance == 'jardin' and a.jardin:
            detalle_alcance = a.jardin.nombre
        elif a.alcance == 'sala':
            detalle_alcance = ", ".join([s.nombre for s in a.salas.all()])
        elif a.alcance == 'docente':
            detalle_alcance = ", ".join([f"{d.last_name}, {d.first_name}" for d in a.docentes.all()])

        writer.writerow([
            a.nombre,
            a.tipo.nombre if a.tipo else "—",
            a.fecha.strftime("%d/%m/%Y"),
            a.hora_inicio.strftime("%H:%M"),
            a.hora_fin.strftime("%H:%M"),
            a.get_alcance_display(),
            detalle_alcance,
            a.obtener_docentes_afectados().count()
        ])

    return response
