from django.core.management.base import BaseCommand
from django.utils import timezone
from jardines.models import Jardin, Sala
from alumnos.models import Alumno, Tutor, Asistencia, MotivoJustificacion
from users.models import Usuario


class Command(BaseCommand):
    help = 'Crea un conjunto de datos de demostración completo y variado.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Creando datos de demostración...")

        # Jardines
        jardin1, _ = Jardin.objects.get_or_create(
            nombre="Jardín Florido",
            direccion="Av. Siempreviva 123",
            coordenadas="-34.6037,-58.3816",
            sector="Zona Norte",
            subprograma="Inicial"
        )
        jardin2, _ = Jardin.objects.get_or_create(
            nombre="Jardín Rayito de Sol",
            direccion="Calle Luna 456",
            coordenadas="-34.6155,-58.3772",
            sector="Zona Sur",
            subprograma="Maternal"
        )

        # Salas
        sala1 = Sala.objects.create(nombre="Sala Roja", turno="mañana", jardin=jardin1, horario_inicio="08:00", horario_fin="12:00")
        sala2 = Sala.objects.create(nombre="Sala Azul", turno="tarde", jardin=jardin1, horario_inicio="13:00", horario_fin="17:00")
        sala3 = Sala.objects.create(nombre="Sala Verde", turno="mañana", jardin=jardin2, horario_inicio="09:00", horario_fin="13:00")
        sala4 = Sala.objects.create(nombre="Sala Amarilla", turno="tarde", jardin=jardin2, horario_inicio="14:00", horario_fin="18:00")
        sala5 = Sala.objects.create(nombre="Sala Roja", turno="mañana", jardin=jardin2, horario_inicio="08:30", horario_fin="12:30")

        # Motivos
        motivo1, _ = MotivoJustificacion.objects.get_or_create(nombre="Turno médico")
        motivo2, _ = MotivoJustificacion.objects.get_or_create(nombre="Enfermedad")
        motivo3, _ = MotivoJustificacion.objects.get_or_create(nombre="Problema familiar")

        # Docente 1 - 1 sola sala
        docente1, _ = Usuario.objects.get_or_create(
            username="ana_docente",
            defaults={"first_name": "Ana", "last_name": "Gómez", "dni": "23.456.789", "is_staff": True}
        )
        docente1.set_password("demo123")
        docente1.save()
        docente1.salas.set([sala1])

        # Docente 2 - 2 salas
        docente2, _ = Usuario.objects.get_or_create(
            username="marco_docente",
            defaults={"first_name": "Marcos", "last_name": "López", "dni": "28.888.888", "is_staff": True}
        )
        docente2.set_password("demo123")
        docente2.save()
        docente2.salas.set([sala2, sala3])

        # Docente 3 - 3 salas
        docente3, _ = Usuario.objects.get_or_create(
            username="laura_docente",
            defaults={"first_name": "Laura", "last_name": "Fernández", "dni": "30.123.456", "is_staff": True}
        )
        docente3.set_password("demo123")
        docente3.save()
        docente3.salas.set([sala3, sala4, sala5])

        # Tutores
        tutor1 = Tutor.objects.create(nombre="Carlos", apellido="Pérez", dni="20.123.456", telefono="1123456789", email="carlos@example.com")
        tutor2 = Tutor.objects.create(nombre="María", apellido="López", dni="21.987.654", telefono="1134567890", email="maria@example.com")
        tutor3 = Tutor.objects.create(nombre="Sandra", apellido="Gómez", dni="27.456.123", telefono="1145678910", email="sandra@example.com")
        tutor4 = Tutor.objects.create(nombre="Lucas", apellido="Martínez", dni="26.222.333", telefono="1178910111", email="lucas@example.com")

        # Alumnos
        alumno1 = Alumno.objects.create(nombre="Juan", apellido="Martínez", dni="33.111.222", sala=sala1, activo=True, fecha_alta=timezone.now())
        alumno1.tutores.set([tutor1])  # 1 tutor

        alumno2 = Alumno.objects.create(nombre="Sofía", apellido="García", dni="44.333.222", sala=sala2, activo=True, fecha_alta=timezone.now())
        alumno2.tutores.set([tutor2, tutor3])  # 2 tutores

        alumno3 = Alumno.objects.create(nombre="Valentina", apellido="Suárez", dni="45.000.123", sala=sala3, activo=True, fecha_alta=timezone.now())
        alumno3.tutores.set([tutor4])  # 1 tutor

        alumno4 = Alumno.objects.create(nombre="Pedro", apellido="Luna", dni="46.100.100", sala=sala5, activo=True, fecha_alta=timezone.now())
        alumno4.tutores.set([tutor1, tutor3])  # 2 tutores

        # Asistencias
        Asistencia.objects.create(alumno=alumno1, fecha=timezone.now().date(), estado="P")
        Asistencia.objects.create(alumno=alumno2, fecha=timezone.now().date(), estado="A")
        Asistencia.objects.create(alumno=alumno3, fecha=timezone.now().date(), estado="J", motivo=motivo1)
        Asistencia.objects.create(alumno=alumno4, fecha=timezone.now().date(), estado="J", motivo=motivo3)

        self.stdout.write(self.style.SUCCESS("✅ Datos de demostración creados exitosamente."))

