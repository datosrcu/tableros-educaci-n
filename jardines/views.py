from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from .models import Subprograma, Jardin, Sala, AsistenciaDocente
from users.decorators import rol_requerido
from django.contrib.auth.decorators import login_required
from users.models import Usuario
from datetime import date
import calendar
import csv

@login_required
@rol_requerido("coordinador", "administrador")
def cargar_subprogramas(request):
    programa_id = request.GET.get("programa_id")
    subprogramas = Subprograma.objects.filter(programa_id=programa_id)
    return JsonResponse([{"id": s.id, "nombre": s.nombre} for s in subprogramas], safe=False)

@login_required
@rol_requerido("coordinador", "administrador")
def cargar_jardines(request):
    programa_id = request.GET.get("programa_id")
    jardines = Jardin.objects.filter(programa_id=programa_id)
    return JsonResponse([{"id": j.id, "nombre": j.nombre} for j in jardines], safe=False)

@login_required
@rol_requerido("coordinador", "administrador")
def validar_docente_turno(request):
    docente_id = request.GET.get("docente_id")
    turno = request.GET.get("turno")
    sala_id = request.GET.get("sala_id")
    qs = Sala.objects.filter(docentes__id=docente_id, turno=turno)
    if sala_id:
        qs = qs.exclude(id=sala_id)
    return JsonResponse({"conflicto": qs.exists()})

@login_required
def subprogramas_por_programa(request):
    programa_id = request.GET.get("programa_id")
    subprogramas = []
    if programa_id:
        subprogramas = list(Subprograma.objects.filter(programa_id=programa_id).values("id", "nombre"))
    return JsonResponse(subprogramas, safe=False)

# ... (vistas de asistencia docente a continuación) ...

@login_required
@rol_requerido("coordinador", "administrador")
def lista_jardines_asistencia(request):
    """
    Lista de jardines para que el coordinador seleccione uno y cargue asistencia docente.
    Si es coordinador, solo ve los jardines de sus programas asignados.
    """
    user = request.user
    if user.rol == "administrador":
        jardines = Jardin.objects.all().select_related("programa")
    else:
        jardines = Jardin.objects.filter(programa__coordinadores=user).select_related("programa")
    
    return render(request, "jardines/asistencia_docente_lista.html", {
        "jardines": jardines
    })

@login_required
@rol_requerido("coordinador", "administrador")
def cargar_asistencia_docente(request, jardin_id):
    """
    Carga masiva de asistencia para los docentes de un jardín específico.
    """
    jardin = get_object_or_404(Jardin, id=jardin_id)
    fecha_str = request.GET.get("fecha", str(date.today()))
    fecha = date.fromisoformat(fecha_str)

    # Obtenemos los docentes vinculados a las salas de este jardín
    docentes = Usuario.objects.filter(
        salas_asignadas__jardin=jardin, 
        rol="docente"
    ).distinct().order_by("last_name")

    if request.method == "POST":
        for docente in docentes:
            estado = request.POST.get(f"estado_{docente.id}")
            observaciones = request.POST.get(f"obs_{docente.id}", "")
            
            if estado:
                AsistenciaDocente.objects.update_or_create(
                    docente=docente,
                    jardin=jardin,
                    fecha=fecha,
                    defaults={
                        "estado": estado,
                        "observaciones": observaciones,
                        "registrado_por": request.user
                    }
                )
        
        messages.success(request, f"Asistencia docente del {fecha} guardada correctamente.")
        return redirect("jardines:cargar_asistencia_docente", jardin_id=jardin.id)

    # Buscar asistencias ya cargadas para esta fecha
    asistencias_existentes = AsistenciaDocente.objects.filter(
        jardin=jardin, 
        fecha=fecha
    )
    asistencias_dict = {a.docente_id: a for a in asistencias_existentes}

    docente_data = []
    for d in docentes:
        docente_data.append({
            "docente": d,
            "asistencia": asistencias_dict.get(d.id)
        })

    return render(request, "jardines/asistencia_docente_form.html", {
        "jardin": jardin,
        "fecha": fecha_str,
        "docente_data": docente_data,
        "ESTADO_CHOICES": AsistenciaDocente.ESTADO_CHOICES
    })

@login_required
@rol_requerido("coordinador", "administrador")
def historial_asistencia_docente(request):
    """
    Historial general de asistencia docente con filtros.
    """
    user = request.user
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    jardin_id = request.GET.get("jardin")

    asistencias = AsistenciaDocente.objects.select_related("docente", "jardin", "registrado_por")

    if user.rol == "coordinador":
        asistencias = asistencias.filter(jardin__programa__coordinadores=user)

    if mes:
        asistencias = asistencias.filter(fecha__month=mes)
    if anio:
        asistencias = asistencias.filter(fecha__year=anio)
    if jardin_id:
        asistencias = asistencias.filter(jardin_id=jardin_id)

    # Para los filtros
    if user.rol == "administrador":
        jardines = Jardin.objects.all()
    else:
        jardines = Jardin.objects.filter(programa__coordinadores=user)

@login_required
@rol_requerido("coordinador", "administrador")
def reporte_asistencia_docente_mensual(request):
    """
    Genera una matriz mensual de asistencia para todos los docentes de un jardín.
    """
    ahora = date.today()
    mes = int(request.GET.get('mes', ahora.month))
    anio = int(request.GET.get('anio', ahora.year))
    jardin_id = request.GET.get('jardin')

    if not jardin_id:
        # Si no hay jardín seleccionado, mostrar lista para elegir
        user = request.user
        if user.rol == "administrador":
            jardines = Jardin.objects.all()
        else:
            jardines = Jardin.objects.filter(programa__coordinadores=user)
        
        return render(request, "jardines/reporte_docente_seleccion.html", {
            "jardines": jardines,
            "meses": range(1, 13),
            "anios": range(2024, ahora.year + 1),
            "mes_sel": mes,
            "anio_sel": anio
        })

    jardin = get_object_or_404(Jardin, id=jardin_id)
    ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
    
    # Docentes del jardín
    docentes = Usuario.objects.filter(
        salas_asignadas__jardin=jardin, 
        rol="docente"
    ).distinct().order_by("last_name")

    # Obtener todas las asistencias del mes
    asistencias = AsistenciaDocente.objects.filter(
        jardin=jardin,
        fecha__year=anio,
        fecha__month=mes
    )
    
    # Mapear asistencias: { docente_id: { dia: estado } }
    mapa_asistencia = {}
    for a in asistencias:
        if a.docente_id not in mapa_asistencia:
            mapa_asistencia[a.docente_id] = {}
        mapa_asistencia[a.docente_id][a.fecha.day] = a.estado

    filas = []
    for d in docentes:
        celdas = []
        presentes = 0
        ausentes = 0
        for dia in range(1, ultimo_dia_mes + 1):
            estado = mapa_asistencia.get(d.id, {}).get(dia, '-')
            celdas.append(estado)
            if estado == 'P': presentes += 1
            if estado == 'A': ausentes += 1
        
        filas.append({
            'docente': d,
            'celdas': celdas,
            'presentes': presentes,
            'ausentes': ausentes
        })

    context = {
        'jardin': jardin,
        'mes': mes,
        'anio': anio,
        'mes_nombre': calendar.month_name[mes].capitalize(),
        'dias': range(1, ultimo_dia_mes + 1),
        'filas': filas,
    }

    if 'export' in request.GET:
        return exportar_asistencia_docente_csv(context)

    return render(request, "jardines/reporte_asistencia_docente_mensual.html", context)

def exportar_asistencia_docente_csv(context):
    """
    Exporta la matriz de asistencia docente a CSV.
    """
    response = HttpResponse(content_type='text/csv')
    filename = f"asistencia_docente_{context['jardin'].nombre}_{context['mes']}_{context['anio']}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    
    # Encabezado
    header = ['Docente'] + [str(d) for d in context['dias']] + ['P', 'A']
    writer.writerow(header)
    
    for fila in context['filas']:
        row = [f"{fila['docente'].last_name}, {fila['docente'].first_name}"] + fila['celdas'] + [fila['presentes'], fila['ausentes']]
        writer.writerow(row)
        
    return response

@login_required
@rol_requerido("coordinador", "administrador")
def resumen_actividad_docente(request):
    """
    Muestra un resumen de los docentes que iniciaron sesión hoy y sus últimas acciones.
    """
    from users.models import AccionAuditoria
    from django.db.models import Max, OuterRef, Subquery
    
    hoy = date.today()
    user = request.user
    
    # Base de docentes a supervisar
    if user.rol == "administrador":
        docentes = Usuario.objects.filter(rol="docente")
    else:
        docentes = Usuario.objects.filter(rol="docente", salas_asignadas__jardin__programa__coordinadores=user).distinct()

    docentes = docentes.order_by("last_name")

    # Obtener asistencias de hoy
    asistencias_hoy = AsistenciaDocente.objects.filter(fecha=hoy).select_related("jardin")
    asistencias_dict = {}
    for a in asistencias_hoy:
        if a.docente_id not in asistencias_dict:
            asistencias_dict[a.docente_id] = []
        asistencias_dict[a.docente_id].append(a)

    # Buscar todas las acciones de hoy para los docentes filtrados
    acciones_hoy = AccionAuditoria.objects.filter(
        fecha__date=hoy,
        usuario__in=docentes
    ).select_related("usuario").order_by("-fecha")
    
    acciones_por_usuario = {}
    for acc in acciones_hoy:
        if acc.usuario_id not in acciones_por_usuario:
            acciones_por_usuario[acc.usuario_id] = []
        acciones_por_usuario[acc.usuario_id].append(acc)

    resumen = []
    for d in docentes:
        asists = asistencias_dict.get(d.id, [])
        accs = acciones_por_usuario.get(d.id, [])
        
        resumen.append({
            "docente": d,
            "asistencias": asists,
            "inicio_sesion": asists[0].hora_ingreso if asists else None,
            "ip": asists[0].ip_address if asists else None,
            "ultima_accion": accs[0] if accs else None,
            "total_acciones": len(accs),
            "activo": len(asists) > 0 or len(accs) > 0
        })

    activos_count = sum(1 for item in resumen if item['activo'])

    return render(request, "jardines/resumen_actividad_docente.html", {
        "resumen": resumen,
        "fecha": hoy,
        "activos_count": activos_count,
    })
# Create your views here.
