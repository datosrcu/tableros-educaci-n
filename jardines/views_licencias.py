import csv
import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, F

from users.decorators import rol_requerido
from users.models import Usuario
from .models import LicenciaDocente, ReemplazanteLicencia, Sala, Programa, Jardin
from .forms import LicenciaDocenteForm

@login_required
@rol_requerido("coordinador", "administrador")
def lista_licencias(request):
    user = request.user
    q = request.GET.get("q", "").strip()
    
    if user.es_admin() or not user.programas_asignados.exists():
        licencias = LicenciaDocente.objects.prefetch_related(
            "reemplazantes_licencia__reemplazante",
            "reemplazantes_licencia__sala__jardin"
        ).select_related("docente").all()
    else:
        programas = user.programas_asignados.all()
        licencias = LicenciaDocente.objects.filter(
            docente__salas_asignadas__jardin__programa__in=programas
        ).prefetch_related(
            "reemplazantes_licencia__reemplazante",
            "reemplazantes_licencia__sala__jardin"
        ).select_related("docente").distinct()
        
    if q:
        licencias = licencias.filter(
            Q(docente__first_name__icontains=q) |
            Q(docente__last_name__icontains=q) |
            Q(docente__username__icontains=q) |
            Q(reemplazantes_licencia__reemplazante__first_name__icontains=q) |
            Q(reemplazantes_licencia__reemplazante__last_name__icontains=q) |
            Q(reemplazantes_licencia__reemplazante__username__icontains=q) |
            Q(motivo__icontains=q)
        ).distinct()

    licencias = licencias.order_by(
        "-fecha_desde",
        "docente__last_name",
        "docente__first_name",
    )
        
    # Calcular días para cada licencia en la lista
    for l in licencias:
        l.dias = (l.fecha_hasta - l.fecha_desde).days + 1
        
    return render(request, "licencias/lista.html", {
        "licencias": licencias,
        "q": q
    })

@login_required
@rol_requerido("coordinador", "administrador")
def ajax_salas_reemplazante(request):
    """
    Retorna en JSON las salas asignadas al docente seleccionado (o todas las salas de la jurisdicción)
    para que la coordinadora elija a qué sala va cada reemplazo.
    """
    docente_id = request.GET.get("docente_id")
    salas_data = []
    
    if docente_id:
        try:
            docente = Usuario.objects.get(pk=docente_id)
            salas = docente.salas_asignadas.select_related("jardin").order_by("jardin__nombre", "nombre")
            for s in salas:
                turno_str = s.get_turno_display() if hasattr(s, 'get_turno_display') else s.turno
                salas_data.append({
                    "id": s.id,
                    "nombre": f"{s.nombre} ({turno_str.capitalize()}) - {s.jardin.nombre}",
                    "turno": s.turno,
                    "es_asignada": True
                })
        except Usuario.DoesNotExist:
            pass

    return JsonResponse({"salas": salas_data})

def _procesar_reemplazantes_post(request, licencia):
    """Guarda la lista de reemplazantes y sus salas asignadas para una licencia."""
    reemplazantes_ids = request.POST.getlist("reemplazante_id[]")
    salas_ids = request.POST.getlist("reemplazante_sala_id[]")
    
    # Limpiar reemplazantes previos
    licencia.reemplazantes_licencia.all().delete()
    
    for i, reemp_id in enumerate(reemplazantes_ids):
        if not reemp_id:
            continue
        try:
            reemp_user = Usuario.objects.get(pk=reemp_id)
            if reemp_user == licencia.docente:
                continue  # Evitar asignarse a sí mismo
                
            sala_id = salas_ids[i] if i < len(salas_ids) and salas_ids[i] else None
            sala_obj = Sala.objects.filter(pk=sala_id).first() if sala_id else None
            
            ReemplazanteLicencia.objects.create(
                licencia=licencia,
                reemplazante=reemp_user,
                sala=sala_obj
            )
        except Usuario.DoesNotExist:
            continue

@login_required
@rol_requerido("coordinador", "administrador")
def crear_licencia(request):
    form = LicenciaDocenteForm(request.POST or None, user=request.user)
    
    # Obtener lista de docentes disponibles para reemplazantes
    from django.db.models.functions import Lower, Coalesce, NullIf
    from django.db.models import Value
    docentes_qs = Usuario.objects.filter(rol__in=["docente", "auxiliar"])
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        docentes_qs = docentes_qs.filter(
            salas_asignadas__jardin__programa__in=programas
        ).distinct()
    docentes_qs = docentes_qs.order_by(
        Coalesce(NullIf(Lower("last_name"), Value("")), NullIf(Lower("first_name"), Value("")), Lower("username")).asc(),
        Lower("first_name").asc(nulls_last=True),
        Lower("username").asc()
    )

    if request.method == "POST":
        if form.is_valid():
            lic = form.save(commit=False)
            # Validación de seguridad: el docente debe pertenecer a la jurisdicción
            if not request.user.es_admin() and request.user.programas_asignados.exists():
                programas = request.user.programas_asignados.all()
                if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El docente seleccionado no pertenece a sus programas.")
            
            lic.creado_por = request.user
            lic.save()
            
            # Guardar reemplazantes con sus salas
            _procesar_reemplazantes_post(request, lic)
            
            messages.success(request, f"Licencia de {lic.docente} registrada con éxito.")
            return redirect("jardines:lista_licencias")
            
    return render(request, "licencias/form.html", {
        "form": form,
        "docentes_reemplazo": docentes_qs,
        "reemplazos_data": [],
        "titulo": "Registrar Licencia"
    })

@login_required
@rol_requerido("coordinador", "administrador")
def editar_licencia(request, pk):
    lic = get_object_or_404(
        LicenciaDocente.objects.prefetch_related("reemplazantes_licencia__reemplazante", "reemplazantes_licencia__sala"),
        pk=pk
    )
    
    # Permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
            raise PermissionDenied("No tiene permiso para editar esta licencia.")
            
    form = LicenciaDocenteForm(request.POST or None, instance=lic, user=request.user)
    
    # Docentes para reemplazos
    from django.db.models.functions import Lower, Coalesce, NullIf
    from django.db.models import Value
    docentes_qs = Usuario.objects.filter(rol__in=["docente", "auxiliar"])
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        docentes_qs = docentes_qs.filter(
            salas_asignadas__jardin__programa__in=programas
        ).distinct()
    docentes_qs = docentes_qs.order_by(
        Coalesce(NullIf(Lower("last_name"), Value("")), NullIf(Lower("first_name"), Value("")), Lower("username")).asc(),
        Lower("first_name").asc(nulls_last=True),
        Lower("username").asc()
    )

    if request.method == "POST":
        if form.is_valid():
            lic = form.save(commit=False)
            if not request.user.es_admin() and request.user.programas_asignados.exists():
                programas = request.user.programas_asignados.all()
                if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El docente seleccionado no pertenece a sus programas.")
                    
            lic.save()
            _procesar_reemplazantes_post(request, lic)
            
            messages.success(request, f"Licencia de {lic.docente} actualizada con éxito.")
            return redirect("jardines:lista_licencias")
    
    # Reemplazos actuales para poblar la vista
    reemplazos_data = [
        {
            "reemplazante_id": r.reemplazante_id,
            "sala_id": r.sala_id or ""
        }
        for r in lic.reemplazantes_licencia.all()
    ]
            
    return render(request, "licencias/form.html", {
        "form": form,
        "licencia": lic,
        "docentes_reemplazo": docentes_qs,
        "reemplazos_data": reemplazos_data,
        "titulo": "Editar Licencia"
    })

@login_required
@rol_requerido("coordinador", "administrador")
def eliminar_licencia(request, pk):
    lic = get_object_or_404(LicenciaDocente, pk=pk)
    
    # Permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
            raise PermissionDenied("No tiene permiso para eliminar esta licencia.")
            
    if request.method == "POST":
        docente_str = str(lic.docente)
        lic.delete()
        messages.success(request, f"Licencia de {docente_str} eliminada correctamente.")
        return redirect("jardines:lista_licencias")
        
    return render(request, "licencias/eliminar_confirmar.html", {
        "licencia": lic
    })

@login_required
@rol_requerido("coordinador", "administrador")
def ver_detalle_licencia(request, pk):
    lic = get_object_or_404(
        LicenciaDocente.objects.prefetch_related(
            "reemplazantes_licencia__reemplazante",
            "reemplazantes_licencia__sala__jardin"
        ).select_related("docente"),
        pk=pk
    )
    
    # Permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
            raise PermissionDenied("No tiene permiso para ver esta licencia.")
            
    lic.dias = (lic.fecha_hasta - lic.fecha_desde).days + 1
    return render(request, "licencias/detalle.html", {
        "licencia": lic
    })

@login_required
@rol_requerido("coordinador", "administrador")
def exportar_licencias_excel(request):
    user = request.user
    
    if user.es_admin() or not user.programas_asignados.exists():
        licencias = LicenciaDocente.objects.prefetch_related(
            "reemplazantes_licencia__reemplazante",
            "reemplazantes_licencia__sala"
        ).select_related("docente").all()
    else:
        programas = user.programas_asignados.all()
        licencias = LicenciaDocente.objects.filter(
            docente__salas_asignadas__jardin__programa__in=programas
        ).prefetch_related(
            "reemplazantes_licencia__reemplazante",
            "reemplazantes_licencia__sala"
        ).select_related("docente").distinct()
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="licencias_docentes.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Docente', 'Tipo de Licencia', 'Turno Afectado', 'Fecha Desde', 'Fecha Hasta', 'Dias', 'Reemplazantes y Salas', 'Motivo'])
    
    for l in licencias:
        dias = (l.fecha_hasta - l.fecha_desde).days + 1
        
        reemplazos_list = []
        for r in l.reemplazantes_licencia.all():
            sala_txt = f" (Sala: {r.sala.nombre})" if r.sala else ""
            reemplazos_list.append(f"{r.reemplazante.last_name}, {r.reemplazante.first_name}{sala_txt}")
        
        reemplazo_str = " | ".join(reemplazos_list) if reemplazos_list else "Sin reemplazo"
        turno_str = l.get_turno_licencia_display() if l.turno_licencia else "Todos los turnos"
        
        writer.writerow([
            f"{l.docente.last_name}, {l.docente.first_name}",
            l.get_tipo_licencia_display(),
            turno_str,
            l.fecha_desde.strftime('%d/%m/%Y'),
            l.fecha_hasta.strftime('%d/%m/%Y'),
            dias,
            reemplazo_str,
            l.motivo
        ])
    return response

@login_required
@rol_requerido("coordinador", "administrador")
def reporte_licencias(request):
    user = request.user
    
    if user.es_admin() or not user.programas_asignados.exists():
        licencias = LicenciaDocente.objects.select_related("docente").all()
    else:
        programas = user.programas_asignados.all()
        licencias = LicenciaDocente.objects.filter(
            docente__salas_asignadas__jardin__programa__in=programas
        ).select_related("docente").distinct()
        
    total_licencias = licencias.count()
    total_dias = 0
    por_tipo = {}
    por_docente = {}
    por_programa = {}
    
    for l in licencias:
        dias = (l.fecha_hasta - l.fecha_desde).days + 1
        total_dias += dias
        
        # Tipo
        tipo_lbl = l.get_tipo_licencia_display()
        por_tipo[tipo_lbl] = por_tipo.get(tipo_lbl, 0) + 1
        
        # Docente
        docente_lbl = f"{l.docente.last_name}, {l.docente.first_name}"
        if docente_lbl not in por_docente:
            por_docente[docente_lbl] = {"cantidad": 0, "dias": 0}
        por_docente[docente_lbl]["cantidad"] += 1
        por_docente[docente_lbl]["dias"] += dias
        
        # Programa
        programas_docente = Programa.objects.filter(jardines__salas__docentes=l.docente).distinct()
        for prog in programas_docente:
            por_programa[prog.nombre] = por_programa.get(prog.nombre, 0) + 1
            
    # Sort results
    ranking_docentes = sorted(por_docente.items(), key=lambda x: x[1]["dias"], reverse=True)[:10]
    tipo_data = sorted(por_tipo.items(), key=lambda x: x[1], reverse=True)
    programa_data = sorted(por_programa.items(), key=lambda x: x[1], reverse=True)
    
    docentes_ranking = []
    for doc, val in ranking_docentes:
        docentes_ranking.append({
            "nombre": doc,
            "cantidad": val["cantidad"],
            "dias": val["dias"]
        })
        
    return render(request, "licencias/reporte.html", {
        "total_licencias": total_licencias,
        "total_dias": total_dias,
        "tipo_data": tipo_data,
        "programa_data": programa_data,
        "docentes_ranking": docentes_ranking
    })

