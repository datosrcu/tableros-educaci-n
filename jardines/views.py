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
from django.utils import timezone

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
    jardines = Jardin.objects.all().select_related("programa").order_by("nombre")
    
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

    # 🔒 Validación de propiedad
    if not request.user.es_admin() and jardin.programa not in request.user.programas_asignados.all():
        raise PermissionDenied("No tiene permiso para cargar asistencia en este espacio.")

    fecha_str = request.GET.get("fecha", str(timezone.localtime(timezone.now()).date()))
    fecha = date.fromisoformat(fecha_str)

    # Obtenemos los docentes vinculados a las salas de este jardín
    docentes = Usuario.objects.filter(
        salas_asignadas__jardin=jardin, 
        rol="docente"
    ).distinct().order_by("last_name")

    if request.method == "POST":
        from .models import LicenciaDocente
        for docente in docentes:
            estado = request.POST.get(f"estado_{docente.id}")
            observaciones = request.POST.get(f"obs_{docente.id}", "")
            
            # Si tiene licencia activa para esta fecha, se fuerza el estado 'L'
            licencia = LicenciaDocente.obtener_licencia_activa(docente, fecha)
            if licencia:
                estado = 'L'
                observaciones = f"Ausente por licencia ({licencia.get_tipo_licencia_display()})."
            
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

    from .models import LicenciaDocente
    docente_data = []
    for d in docentes:
        lic = LicenciaDocente.obtener_licencia_activa(d, fecha)
        docente_data.append({
            "docente": d,
            "asistencia": asistencias_dict.get(d.id),
            "licencia": lic
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

    # 🔒 Base queryset filtrado por programas del coordinador
    if user.es_admin():
        asistencias = AsistenciaDocente.objects.select_related("docente", "jardin", "registrado_por")
        jardines = Jardin.objects.all()
    else:
        asistencias = AsistenciaDocente.objects.filter(
            jardin__programa__in=user.programas_asignados.all()
        ).select_related("docente", "jardin", "registrado_por")
        jardines = Jardin.objects.filter(programa__in=user.programas_asignados.all())

    if mes:
        asistencias = asistencias.filter(fecha__month=mes)
    if anio:
        asistencias = asistencias.filter(fecha__year=anio)
    if jardin_id:
        # 🔒 Doble chequeo: el jardín filtrado debe estar en el queryset ya filtrado
        asistencias = asistencias.filter(jardin_id=jardin_id)

    return render(request, "jardines/asistencia_docente_historial.html", {
        "asistencias": asistencias.order_by("-fecha"),
        "jardines": jardines,
        "mes_sel": mes,
        "anio_sel": anio,
        "jardin_sel": jardin_id,
    })

@login_required
@rol_requerido("coordinador", "administrador")
def reporte_asistencia_docente_mensual(request):
    """
    Genera una matriz mensual de asistencia para todos los docentes de un jardín.
    """
    ahora = timezone.localtime(timezone.now()).date()
    mes = int(request.GET.get('mes', ahora.month))
    anio = int(request.GET.get('anio', ahora.year))
    jardin_id = request.GET.get('jardin')

    if not jardin_id:
        # Si no hay jardín seleccionado, mostrar lista para elegir
        if request.user.es_admin():
            jardines = Jardin.objects.all().order_by("nombre")
        else:
            jardines = Jardin.objects.filter(
                programa__in=request.user.programas_asignados.all()
            ).order_by("nombre")

        return render(request, "jardines/reporte_docente_seleccion.html", {
            "jardines": jardines,
            "meses": range(1, 13),
            "anios": range(2024, ahora.year + 1),
            "mes_sel": mes,
            "anio_sel": anio
        })

    jardin = get_object_or_404(Jardin, id=jardin_id)

    # 🔒 Validación de propiedad
    if not request.user.es_admin() and jardin.programa not in request.user.programas_asignados.all():
        raise PermissionDenied("No tiene permiso para ver el reporte de este espacio.")
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
        licencias = 0
        for dia in range(1, ultimo_dia_mes + 1):
            estado = mapa_asistencia.get(d.id, {}).get(dia, '-')
            celdas.append(estado)
            if estado == 'P': presentes += 1
            if estado == 'A': ausentes += 1
            if estado == 'L': licencias += 1
        
        filas.append({
            'docente': d,
            'celdas': celdas,
            'presentes': presentes,
            'ausentes': ausentes,
            'licencias': licencias
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
    header = ['Docente'] + [str(d) for d in context['dias']] + ['P', 'A', 'L']
    writer.writerow(header)
    
    for fila in context['filas']:
        row = (
            [f"{fila['docente'].last_name}, {fila['docente'].first_name}"]
            + fila['celdas']
            + [fila['presentes'], fila['ausentes'], fila.get('licencias', 0)]
        )
        writer.writerow(row)
        
    return response

@login_required
@rol_requerido("coordinador", "administrador")
def resumen_actividad_docente(request):
    """
    Muestra un resumen de los docentes que iniciaron sesión y sus últimas acciones.
    """
    from users.models import AccionAuditoria
    from django.db.models import Max, OuterRef, Subquery
    
    fecha_str = request.GET.get("fecha")
    if fecha_str:
        try:
            hoy = date.fromisoformat(fecha_str)
        except (ValueError, TypeError):
            hoy = timezone.localtime(timezone.now()).date()
    else:
        hoy = timezone.localtime(timezone.now()).date()
        
    user = request.user


    
    # Base de docentes a supervisar
    if user.es_admin() or not user.programas_asignados.exists():
        docentes = Usuario.objects.filter(rol="docente")
    else:
        programas = user.programas_asignados.all()
        docentes_salas = Usuario.objects.filter(
            rol="docente",
            salas_asignadas__jardin__programa__in=programas
        )
        docentes_asistencia_hoy = Usuario.objects.filter(
            rol="docente",
            asistencias_docente__fecha=hoy,
            asistencias_docente__jardin__programa__in=programas
        )
        docentes = (docentes_salas | docentes_asistencia_hoy).distinct()

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
        
        # Determine if they checked in (fichó) today
        fichado = any(a.fichado for a in asists) if asists else False
        
        # Get coordinates if fichado
        lat = None
        lon = None
        for a in asists:
            if a.fichado and a.latitude and a.longitude:
                lat = float(a.latitude)
                lon = float(a.longitude)
                break
        
        resumen.append({
            "docente": d,
            "asistencias": asists,
            "fichado": fichado,
            "inicio_sesion": asists[0].hora_ingreso if (asists and asists[0].hora_ingreso) else None,
            "ip": asists[0].ip_address if asists else None,
            "ultima_accion": accs[0] if accs else None,
            "total_acciones": len(accs),
            "activo": len(asists) > 0 or len(accs) > 0,
            "lat": lat,
            "lon": lon,
        })

    activos_count = sum(1 for item in resumen if item['activo'])

    return render(request, "jardines/resumen_actividad_docente.html", {
        "resumen": resumen,
        "fecha": hoy,
        "activos_count": activos_count,
    })


from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal, InvalidOperation

@login_required
@rol_requerido("docente")
@require_POST
def registrar_asistencia_docente(request):
    latitude_str = request.POST.get("latitude")
    longitude_str = request.POST.get("longitude")
    
    if not latitude_str or not longitude_str:
        return JsonResponse({"status": "error", "message": "Las coordenadas de ubicación son requeridas al fichar."}, status=400)
        
    try:
        latitude = Decimal(latitude_str).quantize(Decimal('.000001'))
        longitude = Decimal(longitude_str).quantize(Decimal('.000001'))
    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({"status": "error", "message": "Formato de coordenadas no válido."}, status=400)
        
    ahora_local = timezone.localtime(timezone.now())
    hoy = ahora_local.date()
    hora = ahora_local.time()
    ip = request.META.get('REMOTE_ADDR')
    from .models import AsistenciaDocente, inicializar_asistencia_diaria, LicenciaDocente
    from users.models import AccionAuditoria
    from django.core.exceptions import ValidationError
    
    # Check if there is an active license today
    licencia = LicenciaDocente.obtener_licencia_activa(request.user, hoy)
    if licencia:
        return JsonResponse({
            "status": "error",
            "message": f"No puede registrar asistencia porque se encuentra de licencia ({licencia.get_tipo_licencia_display()})."
        }, status=400)

    asistencias = AsistenciaDocente.objects.filter(docente=request.user, fecha=hoy)
    if not asistencias.exists():
        inicializar_asistencia_diaria(request.user, request)
        asistencias = AsistenciaDocente.objects.filter(docente=request.user, fecha=hoy)
        
    if not asistencias.exists():
        return JsonResponse({"status": "error", "message": "No tiene salas o espacios asignados para registrar asistencia."}, status=400)
        
    # Validar si ya fichó hoy
    if asistencias.filter(fichado=True).exists():
        return JsonResponse({"status": "success", "message": "La asistencia ya fue registrada hoy."})
        
    try:
        # Guardar
        for asist in asistencias:
            asist.fichado = True
            asist.estado = 'P'
            asist.hora_ingreso = hora
            asist.ip_address = ip
            asist.latitude = latitude
            asist.longitude = longitude
            asist.observaciones = f"Fichado manual por el docente el {hoy} a las {hora.strftime('%H:%M')} hs."
            asist.save()
    except ValidationError as e:
        error_msg = ", ".join(e.messages) if hasattr(e, "messages") else str(e)
        return JsonResponse({"status": "error", "message": f"Error de validación al guardar: {error_msg}"}, status=400)
        
    # Registrar log
    AccionAuditoria.objects.create(
        usuario=request.user,
        accion="modificacion",
        modelo="AsistenciaDocente",
        objeto_id=request.user.id,
        descripcion=f"Registró asistencia docente (Fichó) el día {hoy.strftime('%d/%m/%Y')} a las {hora.strftime('%H:%M:%S')} hs. Coordenadas: {latitude}, {longitude} - IP: {ip}"
    )
    
    return JsonResponse({"status": "success", "message": "Asistencia registrada correctamente."})


