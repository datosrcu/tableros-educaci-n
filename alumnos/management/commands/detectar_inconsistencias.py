from django.core.management.base import BaseCommand
from jardines.models import Sala
from alumnos.models import Alumno
from users.models import Usuario

class Command(BaseCommand):
    help = 'Detecta inconsistencias como salas sin docentes o alumnos en salas inválidas.'

    def handle(self, *args, **options):
        print("🔍 Analizando consistencia de datos...")

        inconsistencias = False

        # 🧑‍🏫 Salas sin docentes asignados
        salas_sin_docentes = Sala.objects.filter(docentes__isnull=True).distinct()
        if salas_sin_docentes.exists():
            inconsistencias = True
            self.stdout.write(self.style.WARNING(f"\n🚫 Salas sin docentes asignados: {salas_sin_docentes.count()}"))
            for sala in salas_sin_docentes:
                self.stdout.write(f" - Sala: {sala.nombre} ({sala.turno}) - ID: {sala.id}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ Todas las salas tienen al menos un docente asignado."))

        # 👶 Alumnos con salas inexistentes
        alumnos_sin_sala = Alumno.objects.filter(sala__isnull=True)
        if alumnos_sin_sala.exists():
            inconsistencias = True
            self.stdout.write(self.style.WARNING(f"\n🚫 Alumnos sin sala asignada: {alumnos_sin_sala.count()}"))
            for a in alumnos_sin_sala:
                self.stdout.write(f" - ID: {a.id}, Nombre: {a.apellido}, {a.nombre}, DNI: {a.dni}")
            
            confirm = input("\n¿Querés eliminar estos alumnos sin sala? (s/n): ").lower()
            if confirm == 's':
                alumnos_sin_sala.delete()
                self.stdout.write(self.style.SUCCESS("🧹 Alumnos sin sala eliminados."))
            else:
                self.stdout.write("❌ No se eliminó ningún alumno.")
        else:
            self.stdout.write(self.style.SUCCESS("✅ Todos los alumnos están asignados a una sala."))

        # Futuro: podrías agregar aquí validación de docentes en salas eliminadas.

        if not inconsistencias:
            self.stdout.write(self.style.SUCCESS("\n🎉 No se detectaron inconsistencias en el sistema. Todo en orden."))
