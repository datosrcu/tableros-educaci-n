from django.core.management.base import BaseCommand
from alumnos.models import Asistencia

class Command(BaseCommand):
    help = 'Busca y limpia registros de asistencias inválidas.'

    def handle(self, *args, **options):
        print("📋 Buscando asistencias inválidas...")

        asistencias_invalidas = Asistencia.objects.filter(
            alumno__isnull=True
        ) | Asistencia.objects.filter(fecha__isnull=True) | \
            Asistencia.objects.filter(estado__isnull=True) | Asistencia.objects.filter(estado='') | \
            Asistencia.objects.filter(estado__in=['?', 'otro', 'none', 'null']) | \
            Asistencia.objects.filter(docente__isnull=True)

        total = asistencias_invalidas.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron asistencias inválidas."))
            return

        self.stdout.write(self.style.WARNING(f"⚠️  Se encontraron {total} asistencia(s) inválida(s):"))

        for a in asistencias_invalidas:
            self.stdout.write(f" - ID: {a.id}, Fecha: {a.fecha}, Alumno: {a.alumno}, Estado: {a.estado}, Docente: {a.docente}")

        confirm = input("\n¿Querés borrar estos registros? (s/n): ").lower()
        if confirm == 's':
            asistencias_invalidas.delete()
            self.stdout.write(self.style.SUCCESS("🧹 Asistencias inválidas eliminadas correctamente."))
        else:
            self.stdout.write("❌ No se realizó ninguna eliminación.")
