from django.test import TestCase, Client
from django.urls import reverse
from .models import Alumno, Tutor, Sala, MotivoJustificacion, Asistencia
from jardines.models import Jardin, Programa, Subprograma
from users.models import Usuario

class AlumnoTutorTest(TestCase):
    def setUp(self):
        self.docente = Usuario.objects.create_user(
            username='docente_test',
            password='password123',
            rol='docente'
        )
        self.programa = Programa.objects.create(nombre="Prog 1")
        self.jardin = Jardin.objects.create(
            nombre="Jardin 1",
            programa=self.programa,
            direccion="Calle Falsa 123",
            sector="Centro"
        )
        self.sala = Sala.objects.create(nombre="Sala 1", jardin=self.jardin, turno="mañana")
        self.docente.salas_asignadas.add(self.sala)
        
        self.tutor = Tutor.objects.create(
            nombre="Juan",
            apellido="Perez",
            dni="12.345.678"
        )
        self.client = Client()
        self.client.login(username='docente_test', password='password123')

    def test_agregar_alumno_con_tutor(self):
        url = reverse('alumnos:agregar_alumno', kwargs={'sala_id': self.sala.id})
        data = {
            'nombre': 'Pepito',
            'apellido': 'Gomez',
            'dni': '99888777',
            'fecha_nacimiento': '2015-01-01',
            'tutores': [self.tutor.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        alumno = Alumno.objects.get(dni='99888777')
        self.assertEqual(alumno.tutores.count(), 1)
        self.assertEqual(alumno.tutores.first(), self.tutor)

    def test_cargar_asistencia_coordinador(self):
        # Cambiar el rol del usuario a coordinador para permitir la fecha libre
        self.docente.rol = 'coordinador'
        self.docente.save()
        
        alumno = Alumno.objects.create(
            nombre='Maria',
            apellido='Lopez',
            dni='11222333',
            fecha_nacimiento='2016-05-05'
        )
        from alumnos.models import AsignacionSala
        AsignacionSala.objects.create(alumno=alumno, sala=self.sala, activo=True)
        url = reverse('alumnos:cargar_asistencia', kwargs={'sala_id': self.sala.id})
        motivo = MotivoJustificacion.objects.create(nombre="Medico")
        
        data = {
            f'estado_{alumno.id}': 'J',
            f'motivo_{alumno.id}': motivo.id,
            'fecha': '2026-02-18'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        asistencia = Asistencia.objects.get(alumno=alumno, fecha='2026-02-18')
        self.assertEqual(asistencia.estado, 'J')
        self.assertEqual(asistencia.motivo, motivo)

    def test_cargar_asistencia_docente_restricted_to_today(self):
        alumno = Alumno.objects.create(
            nombre='Maria',
            apellido='Lopez',
            dni='11222333',
            fecha_nacimiento='2016-05-05'
        )
        from alumnos.models import AsignacionSala
        from datetime import date
        AsignacionSala.objects.create(alumno=alumno, sala=self.sala, activo=True)
        url = reverse('alumnos:cargar_asistencia', kwargs={'sala_id': self.sala.id})
        motivo = MotivoJustificacion.objects.create(nombre="Medico")
        
        # Docente intenta registrar asistencia en una fecha pasada
        data = {
            f'estado_{alumno.id}': 'J',
            f'motivo_{alumno.id}': motivo.id,
            'fecha': '2026-02-18'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Debe haberse registrado con la fecha enviada en el formulario
        asistencia = Asistencia.objects.get(alumno=alumno, fecha='2026-02-18')
        self.assertEqual(asistencia.estado, 'J')
        self.assertEqual(asistencia.motivo, motivo)
