from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

from alumnos.models import Alumno, AsignacionSala
from jardines.models import Programa, Subprograma, Sala, Jardin

from .models import ProgramaCobro, ResponsableCobro, Pago, MESES_NOMBRES
from .forms import PagoForm

def permiso_cobros_requerido(view_func):
    """
    Decorador que verifica si el usuario es superusuario o está configurado
    como Responsable de Cobro para al menos un programa.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.puede_gestionar_cobros:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("No tiene permisos para acceder a la gestión de cobros.")
    return _wrapped_view


def obtener_meses_adeudados(alumno, programa, hasta_anio, hasta_mes):
    """
    Retorna una lista de diccionarios [{'mes': m, 'anio': y, 'nombre': 'Mes Año'}]
    que el alumno adeuda para el programa especificado
    desde la fecha de ingreso de su asignación activa hasta el periodo especificado (inclusive).
    """
    asignacion = AsignacionSala.objects.filter(
        alumno=alumno,
        sala__jardin__programa=programa,
        activo=True
    ).first()
    
    if not asignacion:
        return []
        
    start_date = asignacion.fecha_ingreso
    start_year = start_date.year
    start_month = start_date.month
    
    # Generar todos los meses a comprobar
    meses_a_comprobar = []
    y, m = start_year, start_month
    while (y < hasta_anio) or (y == hasta_anio and m <= hasta_mes):
        meses_a_comprobar.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
            
    # Obtener pagos del alumno
    pagos_realizados = Pago.objects.filter(
        alumno=alumno,
        programa=programa,
        estado="pagado"
    ).values_list("anio_pagado", "mes_pagado")
    
    pagos_set = set(pagos_realizados)
    
    # Calcular los meses sin pago
    meses_adeudados = []
    for y, m in meses_a_comprobar:
        if (y, m) not in pagos_set:
            meses_adeudados.append({
                "mes": m,
                "anio": y,
                "nombre": f"{MESES_NOMBRES[m]} {y}"
            })
            
    return meses_adeudados


@login_required
@permiso_cobros_requerido
def dashboard_cobros(request):
    user = request.user
    
    # 1. Determinar programas autorizados
    if user.is_superuser or user.rol == "administrador":
        authorized_programs = Programa.objects.filter(configuracion_cobro__activo=True)
    else:
        program_ids = ResponsableCobro.objects.filter(usuario=user).values_list("programa_id", flat=True)
        authorized_programs = Programa.objects.filter(id__in=program_ids, configuracion_cobro__activo=True)
        
    # 2. Consulta Base: Asignaciones de alumnos activas en programas autorizados
    assignments = AsignacionSala.objects.filter(
        activo=True,
        sala__jardin__programa__in=authorized_programs
    ).select_related(
        "alumno", 
        "sala__jardin__programa", 
        "sala__jardin__subprograma", 
        "sala"
    )

    # 3. Filtros
    query = request.GET.get("q", "").strip()
    subprograma_id = request.GET.get("subprograma")
    espacio_id = request.GET.get("espacio")
    sala_id = request.GET.get("sala")
    estado_filtro = request.GET.get("estado")

    
    # Filtros de mes y año para la cuota
    today = timezone.now().date()
    mes_str = request.GET.get("mes")
    anio_str = request.GET.get("anio")
    
    selected_month = int(mes_str) if mes_str else today.month
    selected_year = int(anio_str) if anio_str else today.year

    # Opciones de los filtros del dropdown (acotados a la autorización del usuario)
    subprogramas_choices = Subprograma.objects.filter(programa__in=authorized_programs)
    jardines_choices = Jardin.objects.filter(programa__in=authorized_programs).distinct().order_by("nombre")
    salas_choices = Sala.objects.filter(jardin__programa__in=authorized_programs)

    
    # Opciones de Meses y Años
    meses_choices = [(i, MESES_NOMBRES[i]) for i in range(1, 13)]
    anios_choices = range(today.year - 2, today.year + 3)

    if query:
        assignments = assignments.filter(
            Q(alumno__nombre__icontains=query) |
            Q(alumno__apellido__icontains=query) |
            Q(alumno__dni__icontains=query)
        )
    if subprograma_id:
        assignments = assignments.filter(sala__jardin__subprograma_id=subprograma_id)
    if espacio_id:
        assignments = assignments.filter(sala__jardin_id=espacio_id)
    if sala_id:
        assignments = assignments.filter(sala_id=sala_id)


    rows = []
    prog_cobro_map = {pc.programa_id: pc.importe_mensual for pc in ProgramaCobro.objects.filter(activo=True)}
    
    total_alumnos = len(assignments)
    total_pagados = 0
    
    # Recaudación del mes seleccionado (pagos en estado pagado en el período de cuota seleccionado)
    recaudacion_mes = Pago.objects.filter(
        programa__in=authorized_programs,
        anio_pagado=selected_year,
        mes_pagado=selected_month,
        estado="pagado"
    ).aggregate(total=Sum("importe"))["total"] or 0
    
    # Recaudación acumulada (todos los pagos en estado pagado de todos los tiempos)
    recaudacion_acumulada = Pago.objects.filter(
        programa__in=authorized_programs,
        estado="pagado"
    ).aggregate(total=Sum("importe"))["total"] or 0

    # 🚀 Optimización Bulk:
    alumno_ids = [asn.alumno_id for asn in assignments]
    
    # Consultar todos los pagos realizados ('pagado') para estos alumnos y programas
    pagos_realizados_list = Pago.objects.filter(
        alumno_id__in=alumno_ids,
        programa__in=authorized_programs,
        estado="pagado"
    ).values_list("alumno_id", "programa_id", "anio_pagado", "mes_pagado")
    
    # Agrupar pagos realizados por (alumno_id, programa_id)
    pagos_realizados_map = {}
    for alum_id, prog_id, y, m in pagos_realizados_list:
        key = (alum_id, prog_id)
        if key not in pagos_realizados_map:
            pagos_realizados_map[key] = set()
        pagos_realizados_map[key].add((y, m))
        
    # Consultar los pagos del período actual seleccionado
    current_payments = Pago.objects.filter(
        alumno_id__in=alumno_ids,
        programa__in=authorized_programs,
        anio_pagado=selected_year,
        mes_pagado=selected_month
    )
    current_payments_map = {(p.alumno_id, p.programa_id): p for p in current_payments}
    
    # Mapear fecha de ingreso por (alumno_id, programa_id)
    fecha_ingreso_map = {(asn.alumno_id, asn.sala.jardin.programa_id): asn.fecha_ingreso for asn in assignments}

    for asn in assignments:
        alumno = asn.alumno
        programa = asn.sala.jardin.programa
        subprograma = asn.sala.jardin.subprograma
        sala = asn.sala
        importe_mensual = prog_cobro_map.get(programa.id, 0)
        
        key = (alumno.id, programa.id)
        payment = current_payments_map.get(key)
        
        # Calcular adeudos históricos en memoria
        start_date = fecha_ingreso_map.get(key)
        adeuda_list = []
        if start_date:
            start_year = start_date.year
            start_month = start_date.month
            
            pagos_set = pagos_realizados_map.get(key, set())
            
            y, m = start_year, start_month
            while (y < today.year) or (y == today.year and m <= today.month):
                if (y, m) not in pagos_set:
                    adeuda_list.append(f"{MESES_NOMBRES[m]} {y}")
                m += 1
                if m > 12:
                    m = 1
                    y += 1
                    
        adeuda_str = ", ".join(adeuda_list) if adeuda_list else ""
        
        # Buscar ID del pago en este periodo si existe para descargar comprobante directamente
        pago_periodo_id = payment.id if (payment and payment.estado == "pagado") else None
        
        if payment and payment.estado == "pagado":
            estado_pago = "pagado"
            fecha_pago = payment.fecha_pago
            metodo_pago = payment.get_metodo_pago_display()
            total_pagados += 1
        elif payment:
            estado_pago = "adeuda"
            fecha_pago = payment.fecha_pago
            metodo_pago = payment.get_metodo_pago_display()
        else:
            estado_pago = "adeuda"
            fecha_pago = None
            metodo_pago = None
            
        row = {
            "asignacion": asn,
            "alumno": alumno,
            "programa": programa,
            "subprograma": subprograma,
            "sala": sala,
            "importe_mensual": importe_mensual,
            "estado": estado_pago,
            "fecha_pago": fecha_pago,
            "metodo_pago": metodo_pago,
            "pago_id": pago_periodo_id,
            "meses_adeudados_str": adeuda_str,
            "meses_adeudados_list": adeuda_list,
        }
        
        # Filtro de estado
        if estado_filtro:
            if estado_filtro == estado_pago:
                rows.append(row)
        else:
            rows.append(row)

    total_adeudan = total_alumnos - total_pagados

    context = {
        "rows": rows,
        "subprogramas_choices": subprogramas_choices,
        "jardines_choices": jardines_choices,
        "salas_choices": salas_choices,
        "meses_choices": meses_choices,
        "anios_choices": anios_choices,
        "query": query,
        "selected_subprograma": int(subprograma_id) if subprograma_id else None,
        "selected_espacio": int(espacio_id) if espacio_id else None,
        "selected_sala": int(sala_id) if sala_id else None,
        "selected_estado": estado_filtro,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "total_alumnos": total_alumnos,
        "total_pagados": total_pagados,
        "total_adeudan": total_adeudan,
        "recaudacion_mes": recaudacion_mes,
        "recaudacion_acumulada": recaudacion_acumulada,
    }

    # Verificar si se solicita exportar la planilla
    export_format = request.GET.get("export")
    if export_format == "excel":
        return exportar_cobros_excel(rows, selected_month, selected_year)
    elif export_format == "pdf":
        return exportar_cobros_pdf(rows, selected_month, selected_year)

    return render(request, "cobros/dashboard.html", context)



@login_required
@permiso_cobros_requerido
def registrar_pago(request, asignacion_id):
    asn = get_object_or_404(AsignacionSala, id=asignacion_id)
    alumno = asn.alumno
    programa = asn.sala.jardin.programa
    subprograma = asn.sala.jardin.subprograma
    sala = asn.sala
    
    # Obtener configuración del programa de cobros
    config_cobro = get_object_or_404(ProgramaCobro, programa=programa, activo=True)
    importe = config_cobro.importe_mensual
    
    today = timezone.now().date()
    # Obtener meses adeudados históricos
    adeudos = obtener_meses_adeudados(alumno, programa, today.year, today.month)
    
    # Preseleccionar el mes adeudado más antiguo
    default_mes = today.month
    default_anio = today.year
    if adeudos:
        default_mes = adeudos[0]["mes"]
        default_anio = adeudos[0]["anio"]
        
    if request.method == "POST":
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.registrado_por = request.user
            pago.subprograma = subprograma
            pago.sala = sala
            pago.save()
            
            # Guardar el correo electrónico del alumno si se cargó o editó
            correo_cargado = form.cleaned_data.get("correo_envio")
            if correo_cargado and alumno.email != correo_cargado:
                alumno.email = correo_cargado
                alumno.save()
            
            # Registrar en logs de auditoría del sistema
            from users.models import AccionAuditoria
            AccionAuditoria.objects.create(
                usuario=request.user,
                accion="creacion",
                modelo="Pago",
                objeto_id=pago.id,
                descripcion=f"Registrado pago de ${pago.importe} para el alumno {alumno} en el programa {programa} para el período {pago.mes_pagado}/{pago.anio_pagado} ({pago.get_estado_display()})"
            )
            
            messages.success(request, f"Pago registrado correctamente para el alumno {alumno.apellido}, {alumno.nombre} (Período: {pago.get_mes_pagado_display()} {pago.anio_pagado}).")
            return redirect("cobros:dashboard")
    else:
        # Precompletar el formulario
        form = PagoForm(initial={
            "alumno": alumno,
            "programa": programa,
            "importe": importe,
            "mes_pagado": default_mes,
            "anio_pagado": default_anio,
            "correo_envio": alumno.email or "",
        })
        
    return render(request, "cobros/registrar_pago.html", {
        "form": form,
        "alumno": alumno,
        "programa": programa,
        "asignacion": asn,
        "adeudos": adeudos
    })


@login_required
@permiso_cobros_requerido
def historial_pagos(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    user = request.user
    
    # Programas autorizados para el usuario
    if user.is_superuser or user.rol == "administrador":
        authorized_programs = Programa.objects.filter(configuracion_cobro__activo=True)
    else:
        program_ids = ResponsableCobro.objects.filter(usuario=user).values_list("programa_id", flat=True)
        authorized_programs = Programa.objects.filter(id__in=program_ids, configuracion_cobro__activo=True)
        
    # Listar pagos de este alumno en programas permitidos
    pagos = Pago.objects.filter(
        alumno=alumno,
        programa__in=authorized_programs
    ).select_related("programa", "registrado_por").order_by("-fecha_pago", "-created_at")
    
    return render(request, "cobros/historial.html", {
        "alumno": alumno,
        "pagos": pagos
    })


@login_required
@permiso_cobros_requerido
def descargar_comprobante(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    user = request.user
    
    # Verificar alcance de permisos
    if not (user.is_superuser or user.rol == "administrador"):
        program_ids = ResponsableCobro.objects.filter(usuario=user).values_list("programa_id", flat=True)
        if pago.programa_id not in program_ids:
            raise PermissionDenied("No tiene permisos para descargar comprobantes de este programa.")
            
    # Datos para renderizar el PDF
    template_path = 'cobros/comprobante_pdf.html'
    context = {
        'pago': pago,
        'fecha_emision': timezone.now(),
        'usuario_emisor': user
    }
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Bono_Contribucion_{pago.numero_comprobante}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    # Generar el PDF usando xhtml2pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF', status=500)
    return response


def exportar_cobros_excel(rows, month, year):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    filename = f"planilla_cobros_{month}_{year}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(["Alumno", "DNI", "Subprograma", "Espacio", "Sala", "Importe", "Estado", "Fecha de Pago", "Método", "Deuda Histórica"])
    
    for r in rows:
        writer.writerow([
            f"{r['alumno'].apellido}, {r['alumno'].nombre}",
            r['alumno'].dni,
            r['subprograma'].nombre if r['subprograma'] else "-",
            r['sala'].jardin.nombre,
            f"{r['sala'].nombre} ({r['sala'].get_turno_display()})",
            f"${r['importe_mensual']}",
            "Pagado" if r['estado'] == 'pagado' else "Adeuda",
            r['fecha_pago'].strftime("%d/%m/%Y") if r['fecha_pago'] else "-",
            r['metodo_pago'] or "-",
            r['meses_adeudados_str']
        ])
        
    total_alumnos = len(rows)
    total_pagados = sum(1 for r in rows if r['estado'] == 'pagado')
    total_adeudan = sum(1 for r in rows if r['estado'] != 'pagado')
    recaudacion_total = sum(r['importe_mensual'] for r in rows if r['estado'] == 'pagado')
    
    writer.writerow([])
    writer.writerow(["Resumen de Planilla (Período: " + MESES_NOMBRES[month] + " " + str(year) + ")"])
    writer.writerow(["Total Alumnos", total_alumnos])
    writer.writerow(["Total Pagados", total_pagados])
    writer.writerow(["Total Adeudan", total_adeudan])
    writer.writerow(["Recaudación de Período", f"${recaudacion_total:.2f}"])
    
    return response


def exportar_cobros_pdf(rows, month, year):
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    from django.utils import timezone
    
    total_alumnos = len(rows)
    total_pagados = sum(1 for r in rows if r['estado'] == 'pagado')
    total_adeudan = sum(1 for r in rows if r['estado'] != 'pagado')
    recaudacion_total = sum(r['importe_mensual'] for r in rows if r['estado'] == 'pagado')
    
    context = {
        "rows": rows,
        "month_name": MESES_NOMBRES[month],
        "year": year,
        "fecha_emision": timezone.now(),
        "total_alumnos": total_alumnos,
        "total_pagados": total_pagados,
        "total_adeudan": total_adeudan,
        "recaudacion_total": recaudacion_total,
    }
    
    template_path = 'cobros/planilla_pdf.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="planilla_cobros_{month}_{year}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF', status=500)
    return response

