import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
import time
from django.db.models import Q, Count, Prefetch
from datetime import date
from jardines.models import Jardin, Sala
from alumnos.models import AsignacionSala

hoy = date(2026, 6, 30)
start_of_selected_month = date(2026, 6, 1)
end_of_selected_month = date(2026, 6, 30)

q_activo_mes = Q(
    Q(fecha_ingreso__lte=end_of_selected_month) | Q(alumno__asistencias__fecha__lte=end_of_selected_month)
) & ~Q(
    activo=False,
    fecha_baja__lt=start_of_selected_month
)

q_baja_mes = Q(
    activo=False, 
    fecha_baja__gte=start_of_selected_month, 
    fecha_baja__lte=end_of_selected_month
)

t0 = time.time()
jardines_obj = Jardin.objects.filter(programa__nombre="Espacios lúdicos y de aprendizaje para la primera infancia").select_related('subprograma').order_by('nombre')

salas = Sala.objects.filter(jardin__in=jardines_obj).select_related('jardin').prefetch_related(
    'docentes',
    Prefetch('alumnos_asignados', queryset=AsignacionSala.objects.filter(q_activo_mes), to_attr='activos_list'),
    Prefetch('alumnos_asignados', queryset=AsignacionSala.objects.filter(q_baja_mes), to_attr='bajas_list')
)

espacios_dict = {}
for j in jardines_obj:
    espacios_dict[j.nombre] = {"turnos": {}, "total_activos": 0, "total_bajas": 0}

for s in salas:
    j_nombre = s.jardin.nombre
    if s.turno not in espacios_dict[j_nombre]["turnos"]:
        espacios_dict[j_nombre]["turnos"][s.turno] = {"salas": [], "total_activos": 0, "total_bajas": 0}
        
    docentes = [{"nombres": d.get_full_name() or d.username} for d in s.docentes.all()]
    activos_sala = len(set(a.alumno_id for a in s.activos_list))
    bajas_sala = len(set(a.alumno_id for a in s.bajas_list))
    total_sala = activos_sala + bajas_sala
    
    permanencia = (activos_sala / total_sala * 100) if total_sala > 0 else 0
    desercion = (bajas_sala / total_sala * 100) if total_sala > 0 else 0
    
    espacios_dict[j_nombre]["turnos"][s.turno]["salas"].append({
        "nombre": s.nombre,
        "activos": activos_sala,
        "bajas": bajas_sala,
        "permanencia": permanencia,
        "desercion": desercion,
        "docentes": docentes
    })
    espacios_dict[j_nombre]["turnos"][s.turno]["total_activos"] += activos_sala
    espacios_dict[j_nombre]["turnos"][s.turno]["total_bajas"] += bajas_sala
    
    espacios_dict[j_nombre]["total_activos"] += activos_sala
    espacios_dict[j_nombre]["total_bajas"] += bajas_sala

t1 = time.time()
print("OPTIMIZED TIME:", t1-t0)
print("Keys:", len(espacios_dict))
print("Gorrioncitos activos:", espacios_dict.get('GORRIONCITOS', {}).get('total_activos'))
