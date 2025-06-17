from django.shortcuts import render, redirect, get_object_or_404
from .models import Alumno, Asistencia, MotivoJustificacion
from jardines.models import Sala
from datetime import date, datetime
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from .forms import AlumnoForm, TutorForm, EditarAlumnoForm

@login_required
def dashboard_docente(request):
    salas = request.user.salas_asignadas.all()
    return render(request, 'docentes/dashboard.html', {'salas': salas})

@login_required
def cargar_asistencia(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if sala not in request.user.salas_asignadas.all():
        return render(request, 'docentes/permiso_denegado.html', status=403)

    # 🆕 Obtenemos la fecha desde el formulario o usamos hoy
    fecha_str = request.GET.get('fecha') or request.POST.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    alumnos = Alumno.objects.filter(sala=sala, activo=True)
    motivos = MotivoJustificacion.objects.all()

    if request.method == 'POST':
        for alumno in alumnos:
            estado = request.POST.get(f'estado_{alumno.id}')
            motivo_id = request.POST.get(f'motivo_{alumno.id}')
            motivo = MotivoJustificacion.objects.filter(id=motivo_id).first() if estado == 'justificado' else None
            if estado:
                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    fecha=fecha,
                    defaults={
                        'estado': estado,
                        'motivo': motivo,
                        'docente': request.user
                    }
                )
        
        return redirect('alumnos:cargar_asistencia', sala_id=sala.id)

    # Buscamos asistencias existentes para esa fecha
    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos, fecha=fecha
    )
    asistencias_dict = {a.alumno_id: a.estado for a in asistencias_existentes}
    asistencias_dict_motivo = {
    a.alumno_id: a.motivo_id for a in asistencias_existentes if a.motivo
}

    return render(request, 'docentes/asistencia_form.html', {
        'sala': sala,
        'alumnos': alumnos,
        'fecha': fecha,
        'asistencias_dict': asistencias_dict,
        'motivos': motivos
    })

@login_required
def ver_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    asistencias = Asistencia.objects.filter(alumno=alumno)
    if mes and anio:
        asistencias = asistencias.filter(
            fecha__month=int(mes),
            fecha__year=int(anio)
        )
    
    resumen = asistencias.values('estado').annotate(total=Count('estado'))

    return render(request, 'docentes/alumno_detalle.html', {
        'alumno': alumno,
        'asistencias': asistencias.order_by('-fecha'),
        'resumen': resumen,
        'mes': mes,
        'anio': anio,
    })

@login_required
def alumnos_por_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if sala not in request.user.salas_asignadas.all():
        return render(request, 'docentes/permiso_denegado.html', status=403)

    alumnos = Alumno.objects.filter(sala=sala)

    if request.method == 'POST':
        for alumno in alumnos:
            activo_checkbox = request.POST.get(f'activo_{alumno.id}')
            nuevo_estado = bool(activo_checkbox)

            if alumno.activo != nuevo_estado:
                alumno.activo = nuevo_estado
                alumno.fecha_baja = None if nuevo_estado else date.today()
                alumno.save()

        return redirect('alumnos:alumnos_por_sala', sala_id=sala.id)

    return render(request, 'docentes/alumnos_por_sala.html', {
        'sala': sala,
        'alumnos': alumnos
    })

@login_required
def ver_asistencias(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if sala not in request.user.salas_asignadas.all():
        return render(request, 'docentes/permiso_denegado.html', status=403)

    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    alumnos = Alumno.objects.filter(sala=sala, id__isnull=False)
    asistencias = Asistencia.objects.filter(alumno__in=alumnos, fecha=fecha).select_related('motivo')

    asistencias_dict = {a.alumno_id: a for a in asistencias}

    return render(request, 'docentes/ver_asistencias.html', {
        'sala': sala,
        'fecha': fecha,
        'alumnos': alumnos,
        'asistencias_dict': asistencias_dict
    })

def agregar_alumno(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if sala not in request.user.salas_asignadas.all():
        return render(request, 'docentes/permiso_denegado.html', status=403)

    if request.method == 'POST':
        alumno_form = AlumnoForm(request.POST)
        tutor_form = TutorForm(request.POST)

        if alumno_form.is_valid() and tutor_form.is_valid():
            alumno = alumno_form.save(commit=False)
            alumno.sala = sala
            alumno.activo = True
            alumno.save()

            # Guardar tutor nuevo si se ingresó
            if tutor_form.cleaned_data.get('dni'):
                nuevo_tutor = tutor_form.save()
                alumno.tutores.add(nuevo_tutor)

            # Asociar tutores ya existentes
            for tutor in alumno_form.cleaned_data['tutores_existentes']:
                alumno.tutores.add(tutor)

            return redirect('alumnos:alumnos_por_sala', sala_id=sala.id)
    else:
        alumno_form = AlumnoForm()
        tutor_form = TutorForm()

    return render(request, 'docentes/agregar_alumno.html', {
        'alumno_form': alumno_form,
        'tutor_form': tutor_form,
        'sala': sala
    })

@login_required
def editar_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)

    if alumno.sala not in request.user.salas_asignadas.all():
        return render(request, 'docentes/permiso_denegado.html', status=403)

    if request.method == 'POST':
        form = EditarAlumnoForm(request.POST, instance=alumno)
        if form.is_valid():
            form.save()
            return redirect('alumnos:alumnos_por_sala', sala_id=alumno.sala.id)
    else:
        form = EditarAlumnoForm(instance=alumno)

    return render(request, 'docentes/editar_alumno.html', {
        'form': form,
        'alumno': alumno
    })

# Create your views here.
