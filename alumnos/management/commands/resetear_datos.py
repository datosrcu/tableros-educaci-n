from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Asistencia, Tutor
from jardines.models import Sala, Jardin
from users.models import Usuario

class Command(BaseCommand):
    help = 'Elimina todos los datos del sistema para reiniciar (modo pruebas).'

    def handle(self, *args, **options):
        confirm = input("⚠️ ¿Estás seguro de que querés borrar todos los datos? Esto no se puede deshacer. (s/n): ").lower()
        if confirm != 's':
            self.stdout.write("❌ Operación cancelada.")
            return

        # Borrar todo con el orden correcto para evitar errores de claves foráneas
        self.stdout.write("🚨 Eliminando asistencias...")
        Asistencia.objects.all().delete()

        self.stdout.write("🚨 Eliminando alumnos...")
        Alumno.objects.all().delete()

        self.stdout.write("🚨 Eliminando tutores...")
        Tutor.objects.all().delete()

        self.stdout.write("🚨 Eliminando salas...")
        Sala.objects.all().delete()

        self.stdout.write("🚨 Eliminando jardines...")
        Jardin.objects.all().delete()

        # Eliminar usuarios que no sean superusuarios
        self.stdout.write("🚨 Eliminando usuarios (excepto superusuarios)...")
        Usuario.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("✅ Todos los datos fueron eliminados correctamente."))
