import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Usuario

print("Creando superusuario 'admin'...")
if not Usuario.objects.filter(username='admin').exists():
    Usuario.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Admin creado con password 'admin123'")

print("Creando usuario 'coordinador_test'...")
if not Usuario.objects.filter(username='coordinador_test').exists():
    Usuario.objects.create_user('coordinador_test', 'coordinador@example.com', 'coordinador123', rol='coordinador', first_name='Coordinador', last_name='Test')
    print("Coordinador creado con password 'coordinador123'")

print("Creando usuario 'docente_test'...")
if not Usuario.objects.filter(username='docente_test').exists():
    Usuario.objects.create_user('docente_test', 'docente@example.com', 'docente123', rol='docente', first_name='Docente', last_name='Test')
    print("Docente creado con password 'docente123'")

from alumnos.models import MotivoJustificacion
nuevos_motivos = [
    "Problemas de salud",
    "Cita médica / Odontológica",
    "Trámites familiares",
    "Problemas de transporte",
    "Viaje familiar",
    "Emergencia familiar",
    "Clima adverso"
]
for motivo in nuevos_motivos:
    MotivoJustificacion.objects.get_or_create(nombre=motivo)
print("Motivos de justificación cargados.")

print("Base de datos purgada y cuentas base creadas exitosamente.")
