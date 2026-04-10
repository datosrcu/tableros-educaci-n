import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from alumnos.models import Alumno, AsignacionSala, Asistencia

print("Starting data migration...")

alumnos = Alumno.objects.all()
for alumno in alumnos:
    # 1. Crear AsignacionSala para la sala histórica vinculada
    asignacion, created = AsignacionSala.objects.get_or_create(
        alumno=alumno,
        sala=alumno.sala,
        defaults={
            'activo': alumno.activo,
            'fecha_baja': alumno.fecha_baja
        }
    )
    if created:
        print(f"Created AsignacionSala for {alumno}")

# 2. Popular Asistencia.sala
asistencias = Asistencia.objects.all()
updated_count = 0
for a in asistencias:
    if not a.sala:
        a.sala = a.alumno.sala # Usar la sala histórica en la que estaba ese alumno
        a.save()
        updated_count += 1
print(f"Updated {updated_count} Asistencia records.")

print("Data migration completed successfully.")
