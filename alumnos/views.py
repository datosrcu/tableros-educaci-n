from django.shortcuts import render, redirect, get_object_or_404
from datetime import date, datetime
from django.db.models import Count
from django.contrib.auth.decorators import login_required

from .models import Alumno, Asistencia, MotivoJustificacion
from .forms import AlumnoForm, TutorForm, EditarAlumnoForm

from jardines.models import Sala
from jardines.permissions import validar_sala_para_usuario


@login_required
def dashboard_docente(request):
    if request.user.rol != "docente" and not request.user.is_superuser:
        return render(request, "docentes/permiso_denegado.html", status=403)

    salas = request.user.salas_asignadas.all()
    return render(request, 'alumnos/dashboard_docente.html', {'salas': salas})



@login_required
def cargar_asistencia(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    validar_sala_para_usuario(request.user, sala)

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
            estado_raw = request.POST.get(f'estado_{alumno.id}', 'P')

            estado = 'P'
            motivo = None

            if estado_raw == 'A':
                estado = 'A'
            elif estado_raw.startswith('J-'):
                estado = 'J'
                motivo_id = estado_raw.split('-')[1]
                motivo = MotivoJustificacion.objects.filter(id=motivo_id).first()

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

    asistencias_existentes = Asistencia.objects.filter(
        alumno__in=alumnos, fecha=fecha
    )
    asistencias_dict = {a.alumno_id: a.estado for a in asistencias_existentes}

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
    validar_sala_para_usuario(request.user, alumno.sala)

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
        'año': anio,
    })


@login_required
def alumnos_por_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    validar_sala_para_usuario(request.user, sala)

    alumnos = Alumno.objects.filter(
        sala=sala,
        nombre__gt='',
        apellido__gt='',
        dni__gt=''
    )

    if request.method == 'POST':
        for alumno in alumnos:
            activo = request.POST.get(f'activo_{alumno.id}') == 'on'

            if alumno.activo != activo:
                alumno.activo = activo
                alumno.fecha_baja = None if activo else date.today()
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

@login_required
def agregar_alumno(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    validar_sala_para_usuario(request.user, sala)

    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.sala = sala
            alumno.save()
            form.save_m2m()
            return redirect('alumnos:alumnos_por_sala', sala_id=sala.id)
    else:
        form = AlumnoForm()

    return render(request, 'docentes/agregar_alumno.html', {
        'form': form,
        'sala': sala
    })


@login_required
def editar_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    validar_sala_para_usuario(request.user, alumno.sala)

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
