import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, F

from users.decorators import rol_requerido
from users.models import Usuario
from .models import LicenciaDocente, Programa, Jardin
from .forms import LicenciaDocenteForm

@login_required
@rol_requerido("coordinador", "administrador")
def lista_licencias(request):
    user = request.user
    q = request.GET.get("q", "").strip()
    
    if user.es_admin() or not user.programas_asignados.exists():
        licencias = LicenciaDocente.objects.select_related("docente", "reemplazante").all()
    else:
        programas = user.programas_asignados.all()
        licencias = LicenciaDocente.objects.filter(
            docente__salas_asignadas__jardin__programa__in=programas
        ).select_related("docente", "reemplazante").distinct()
        
    if q:
        licencias = licencias.filter(
            Q(docente__first_name__icontains=q) |
            Q(docente__last_name__icontains=q) |
            Q(docente__username__icontains=q) |
            Q(reemplazante__first_name__icontains=q) |
            Q(reemplazante__last_name__icontains=q) |
            Q(reemplazante__username__icontains=q) |
            Q(motivo__icontains=q)
        ).distinct()

    licencias = licencias.order_by(
        F("reemplazante__last_name").asc(nulls_last=True),
        F("reemplazante__first_name").asc(nulls_last=True),
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
def crear_licencia(request):
    form = LicenciaDocenteForm(request.POST or None, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            lic = form.save(commit=False)
            # Validación de seguridad: el docente debe pertenecer a la jurisdicción
            if not request.user.es_admin() and request.user.programas_asignados.exists():
                programas = request.user.programas_asignados.all()
                if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El docente seleccionado no pertenece a sus programas.")
                if lic.reemplazante and not lic.reemplazante.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El reemplazante seleccionado no pertenece a sus programas.")
            
            lic.creado_por = request.user
            lic.save()
            messages.success(request, f"Licencia de {lic.docente} registrada con éxito.")
            return redirect("jardines:lista_licencias")
            
    return render(request, "licencias/form.html", {
        "form": form,
        "titulo": "Registrar Licencia"
    })

@login_required
@rol_requerido("coordinador", "administrador")
def editar_licencia(request, pk):
    lic = get_object_or_404(LicenciaDocente, pk=pk)
    
    # Permisos
    if not request.user.es_admin() and request.user.programas_asignados.exists():
        programas = request.user.programas_asignados.all()
        if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
            raise PermissionDenied("No tiene permiso para editar esta licencia.")
            
    form = LicenciaDocenteForm(request.POST or None, instance=lic, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            lic = form.save(commit=False)
            # Validación de seguridad adicional
            if not request.user.es_admin() and request.user.programas_asignados.exists():
                programas = request.user.programas_asignados.all()
                if not lic.docente.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El docente seleccionado no pertenece a sus programas.")
                if lic.reemplazante and not lic.reemplazante.salas_asignadas.filter(jardin__programa__in=programas).exists():
                    raise PermissionDenied("El reemplazante seleccionado no pertenece a sus programas.")
                    
            lic.save()
            messages.success(request, f"Licencia de {lic.docente} actualizada con éxito.")
            return redirect("jardines:lista_licencias")
            
    return render(request, "licencias/form.html", {
        "form": form,
        "licencia": lic,
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
    lic = get_object_or_404(LicenciaDocente, pk=pk)
    
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
        licencias = LicenciaDocente.objects.select_related("docente", "reemplazante").all()
    else:
        programas = user.programas_asignados.all()
        licencias = LicenciaDocente.objects.filter(
            docente__salas_asignadas__jardin__programa__in=programas
        ).select_related("docente", "reemplazante").distinct()
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="licencias_docentes.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Docente', 'Tipo de Licencia', 'Fecha Desde', 'Fecha Hasta', 'Dias', 'Reemplazante', 'Motivo'])
    
    for l in licencias:
        dias = (l.fecha_hasta - l.fecha_desde).days + 1
        reemplazo = f"{l.reemplazante.last_name}, {l.reemplazante.first_name}" if l.reemplazante else "Sin reemplazo"
        writer.writerow([
            f"{l.docente.last_name}, {l.docente.first_name}",
            l.get_tipo_licencia_display(),
            l.fecha_desde.strftime('%d/%m/%Y'),
            l.fecha_hasta.strftime('%d/%m/%Y'),
            dias,
            reemplazo,
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
        
        # Programa (Since teacher can be in multiple programs via rooms, attribute the license to those programs)
        programas_docente = Programa.objects.filter(jardines__salas__docentes=l.docente).distinct()
        for prog in programas_docente:
            por_programa[prog.nombre] = por_programa.get(prog.nombre, 0) + 1
            
    # Sort results
    ranking_docentes = sorted(por_docente.items(), key=lambda x: x[1]["dias"], reverse=True)[:10]
    tipo_data = sorted(por_tipo.items(), key=lambda x: x[1], reverse=True)
    programa_data = sorted(por_programa.items(), key=lambda x: x[1], reverse=True)
    
    # Formatear el ranking de docentes para facilitar uso en templates
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
