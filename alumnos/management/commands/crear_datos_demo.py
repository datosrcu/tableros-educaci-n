from django.core.management.base import BaseCommand
from django.utils import timezone
from random import choice
from datetime import timedelta, time

from jardines.models import Jardin, Sala
from users.models import Usuario
from alumnos.models import Alumno, Tutor, Asistencia, MotivoJustificacion

class Command(BaseCommand):
    help = 'Crea datos de ejemplo para pruebas del sistema de gestión escolar.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Creando datos de demostración...")

        # Crear jardín
        jardin, _ = Jardin.objects.get_or_create(nombre="Jardín Modelo")

        # Crear salas
        sala_m, _ = Sala.objects.get_or_create(
            nombre="Sala Roja",
            turno="mañana",
            jardin=jardin,
        defaults={
            "horario_inicio": time(8, 0),
            "horario_fin": time(12, 0)
            }
        )

        sala_t, _ = Sala.objects.get_or_create(
        nombre="Sala Azul",
        turno="tarde",
        jardin=jardin,
        defaults={
            "horario_inicio": time(13, 0),
            "horario_fin": time(17, 0)
            }
        )

        # Crear docentes
        docente1, _ = Usuario.objects.get_or_create(
            username="docente1",
            defaults={
                "first_name": "Lucía",
                "last_name": "Pérez",
                "dni": "20.123.456",
                "es_docente": True,
                "is_active": True,
                "email": "lucia@example.com"
            }
        )
        docente1.set_password("docente123")
        docente1.save()
        docente1.salas_asignadas.add(sala_m)

        docente2, _ = Usuario.objects.get_or_create(
            username="docente2",
            defaults={
                "first_name": "Carlos",
                "last_name": "Gómez",
                "dni": "23.456.789",
                "es_docente": True,
                "is_active": True,
                "email": "carlos@example.com"
            }
        )
        docente2.set_password("docente123")
        docente2.save()
        docente2.salas_asignadas.add(sala_t)

        # Crear motivos
        motivo1, _ = MotivoJustificacion.objects.get_or_create(nombre="Enfermedad")
        motivo2, _ = MotivoJustificacion.objects.get_or_create(nombre="Turno médico")

        estados = ['P', 'A', 'J']

        # Crear tutores, alumnos y asistencias
        for i in range(3):
            tutor = Tutor.objects.create(
                nombre=f"Tutor{i+1}",
                apellido="García",
                dni=f"25.111.11{i}",
                telefono="1111111111",
                email=f"tutor{i+1}@email.com"
            )

            alumno = Alumno.objects.create(
                nombre=f"Alumno{i+1}",
                apellido="Prueba",
                dni=f"44.222.22{i}",
                sala=sala_m,
                activo=True
            )
            alumno.tutores.add(tutor)

            for d in range(3):  # 3 días de asistencia
                fecha = timezone.now().date() - timedelta(days=d)
                estado = choice(estados)
                motivo = motivo1 if estado == 'J' else None
                Asistencia.objects.create(
                    alumno=alumno,
                    docente=docente1,
                    fecha=fecha,
                    estado=estado,
                    motivo=motivo
                )

        for i in range(3):
            tutor = Tutor.objects.create(
                nombre=f"Tutora{i+1}",
                apellido="Martínez",
                dni=f"26.222.22{i}",
                telefono="2222222222",
                email=f"tutora{i+1}@email.com"
            )

            alumno = Alumno.objects.create(
                nombre=f"Alumna{i+1}",
                apellido="Test",
                dni=f"55.333.33{i}",
                sala=sala_t,
                activo=True
            )
            alumno.tutores.add(tutor)

            for d in range(3):
                fecha = timezone.now().date() - timedelta(days=d)
                estado = choice(estados)
                motivo = motivo2 if estado == 'J' else None
                Asistencia.objects.create(
                    alumno=alumno,
                    docente=docente2,
                    fecha=fecha,
                    estado=estado,
                    motivo=motivo
                )

        self.stdout.write(self.style.SUCCESS("✅ Datos demo generados correctamente."))
        self.stdout.write(self.style.SUCCESS("👤 Usuarios de prueba:"))
        self.stdout.write("  • Usuario: docente1 / Contraseña: docente123")
        self.stdout.write("  • Usuario: docente2 / Contraseña: docente123")
