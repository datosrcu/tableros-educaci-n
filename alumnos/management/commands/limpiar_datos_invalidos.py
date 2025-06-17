from django.core.management.base import BaseCommand
from alumnos.models import Alumno

class Command(BaseCommand):
    help = 'Busca y limpia registros de alumnos inválidos o incompletos.'

    def handle(self, *args, **options):
        print("📋 Buscando alumnos inválidos...")

        alumnos_invalidos = Alumno.objects.filter(
            nombre__isnull=True
        ) | Alumno.objects.filter(nombre='') | \
            Alumno.objects.filter(apellido__isnull=True) | Alumno.objects.filter(apellido='') | \
            Alumno.objects.filter(dni__isnull=True) | Alumno.objects.filter(dni='') | \
            Alumno.objects.filter(sala__isnull=True)

        total = alumnos_invalidos.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron alumnos inválidos."))
            return

        self.stdout.write(self.style.WARNING(f"⚠️  Se encontraron {total} alumno(s) inválido(s):"))

        for a in alumnos_invalidos:
            self.stdout.write(f" - ID: {a.id or 'Sin ID'}, Nombre: {a.nombre} {a.apellido}, DNI: {a.dni}, Sala: {a.sala}")

        confirm = input("\n¿Querés borrar estos registros? (s/n): ").lower()
        if confirm == 's':
            alumnos_invalidos.delete()
            self.stdout.write(self.style.SUCCESS("🧹 Alumnos inválidos eliminados correctamente."))
        else:
            self.stdout.write("❌ No se realizó ninguna eliminación.")
