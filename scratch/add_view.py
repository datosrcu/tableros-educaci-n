with open("alumnos/views.py", "a", encoding="utf-8") as f:
    f.write("""

@login_required
@solo_docente
def resumen_mensual_docente(request):
    \"\"\"
    Vista de solo lectura que muestra la tabla mensual de asistencias de los alumnos
    de las salas asignadas al docente, filtrada por mes y año.
    \"\"\"
    from django.db.models import Count
    
    ahora = timezone.localdate()
    mes = int(request.GET.get('mes', ahora.month))
    anio = int(request.GET.get('anio', ahora.year))
    sala_id = request.GET.get('sala')
    
    # Obtener rango de días del mes
    ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
    dias_mes = [date(anio, mes, d) for d in range(1, ultimo_dia_mes + 1)]
    
    # Filtrar salas del docente
    salas = request.user.salas_asignadas.select_related("jardin", "jardin__programa").all().order_by("nombre")
    
    sala_seleccionada = None
    if sala_id:
        try:
            sala_seleccionada = next((s for s in salas if s.id == int(sala_id)), None)
            salas_filtro = [sala_seleccionada] if sala_seleccionada else salas
        except ValueError:
            salas_filtro = salas
    else:
        salas_filtro = salas
        
    alumnos = Alumno.objects.filter(sala__in=salas_filtro, activo=True).select_related('sala').order_by('sala__nombre', 'apellido', 'nombre')
    
    # Obtener todas las asistencias del mes para estos alumnos
    asistencias = Asistencia.objects.filter(
        alumno__in=alumnos,
        fecha__year=anio,
        fecha__month=mes
    ).values('alumno_id', 'fecha', 'estado')
    
    # data_asistencia = { alumno_id: { dia: estado } }
    data_asistencia = {}
    for a in asistencias:
        aid = a['alumno_id']
        fecha = a['fecha']
        if aid not in data_asistencia:
            data_asistencia[aid] = {}
        data_asistencia[aid][fecha.day] = a['estado']
        
    # Organizar filas para la vista por sala
    # [{ sala: Sala, alumnos: [{ alumno: Alumno, dias: [estado_dia1, estado_dia2, ...] }] }]
    datos_por_sala = {}
    for sala in salas_filtro:
        datos_por_sala[sala.id] = {
            'sala': sala,
            'alumnos': []
        }
        
    for alumno in alumnos:
        fila_alumno = {
            'alumno': alumno,
            'dias': []
        }
        for dia in range(1, ultimo_dia_mes + 1):
            estado = data_asistencia.get(alumno.id, {}).get(dia, '-')
            fila_alumno['dias'].append(estado)
            
        if alumno.sala_id in datos_por_sala:
            datos_por_sala[alumno.sala_id]['alumnos'].append(fila_alumno)
            
    # Filtrar salas que no tienen alumnos (opcional, pero deja el reporte mas limpio)
    datos_por_sala_list = [d for d in datos_por_sala.values() if d['alumnos']]
        
    context = {
        'mes': mes,
        'anio': anio,
        'dias_mes': dias_mes,
        'salas': salas,
        'sala_seleccionada': sala_seleccionada,
        'datos_por_sala': datos_por_sala_list,
        'meses_opciones': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ],
        'anios_opciones': range(2024, ahora.year + 2)
    }
    
    return render(request, "alumnos/resumen_mensual_docente.html", context)
""")
