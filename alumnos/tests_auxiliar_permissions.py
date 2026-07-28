from django.test import TestCase, Client
from django.urls import reverse
from alumnos.models import Alumno, Sala, AsignacionSala
from jardines.models import Jardin, Programa
from users.models import Usuario

class AuxiliarPermissionsTest(TestCase):
    def setUp(self):
        self.programa = Programa.objects.create(nombre="Programa Test")
        self.jardin = Jardin.objects.create(
            nombre="Jardin Test",
            programa=self.programa,
            direccion="Calle 1",
            sector="Norte"
        )
        self.sala = Sala.objects.create(nombre="Sala Test", jardin=self.jardin, turno="mañana")

        # Crear Usuario Docente
        self.docente = Usuario.objects.create_user(
            username='docente_user',
            password='password123',
            rol='docente'
        )
        self.docente.salas_asignadas.add(self.sala)

        # Crear Usuario Auxiliar
        self.auxiliar = Usuario.objects.create_user(
            username='auxiliar_user',
            password='password123',
            rol='auxiliar'
        )
        self.auxiliar.salas_asignadas.add(self.sala)

        # Crear Alumno y Asignación
        self.alumno = Alumno.objects.create(
            nombre='Carlitos',
            apellido='Perez',
            dni='44555666',
            fecha_nacimiento='2018-01-01'
        )
        self.asignacion = AsignacionSala.objects.create(alumno=self.alumno, sala=self.sala, activo=True)

        self.client_auxiliar = Client()
        self.client_auxiliar.login(username='auxiliar_user', password='password123')

        self.client_docente = Client()
        self.client_docente.login(username='docente_user', password='password123')

    def test_auxiliar_lectura_permitida(self):
        """Auxiliar puede ver dashboard, lista de alumnos por sala, detalle y asistencias."""
        response_dashboard = self.client_auxiliar.get(reverse('alumnos:dashboard_docente'))
        self.assertEqual(response_dashboard.status_code, 200)

        response_sala = self.client_auxiliar.get(reverse('alumnos:alumnos_por_sala', kwargs={'sala_id': self.sala.id}))
        self.assertEqual(response_sala.status_code, 200)

        response_detalle = self.client_auxiliar.get(reverse('alumnos:detalle_alumno', kwargs={'alumno_id': self.alumno.id}))
        self.assertEqual(response_detalle.status_code, 200)

        response_asistencias = self.client_auxiliar.get(reverse('alumnos:ver_asistencias', kwargs={'sala_id': self.sala.id}))
        self.assertEqual(response_asistencias.status_code, 200)

    def test_auxiliar_denegado_agregar_alumno(self):
        """Auxiliar recibe 403 al intentar acceder a agregar_alumno."""
        url = reverse('alumnos:agregar_alumno', kwargs={'sala_id': self.sala.id})
        response = self.client_auxiliar.get(url)
        self.assertEqual(response.status_code, 403)

    def test_auxiliar_denegado_cargar_asistencia(self):
        """Auxiliar recibe 403 al intentar acceder a cargar_asistencia."""
        url = reverse('alumnos:cargar_asistencia', kwargs={'sala_id': self.sala.id})
        response = self.client_auxiliar.get(url)
        self.assertEqual(response.status_code, 403)

    def test_auxiliar_denegado_editar_alumno(self):
        """Auxiliar recibe 403 al intentar acceder a editar_alumno."""
        url = reverse('alumnos:editar_alumno', kwargs={'alumno_id': self.alumno.id})
        response = self.client_auxiliar.get(url)
        self.assertEqual(response.status_code, 403)

    def test_auxiliar_denegado_post_alumnos_por_sala(self):
        """Auxiliar recibe 403 al intentar realizar un POST en alumnos_por_sala para modificar bajas."""
        url = reverse('alumnos:alumnos_por_sala', kwargs={'sala_id': self.sala.id})
        data = {
            'alumnos_renderizados': [self.alumno.id],
            f'motivo_baja_{self.alumno.id}': 'Prueba de baja'
        }
        response = self.client_auxiliar.post(url, data)
        self.assertEqual(response.status_code, 403)

    def test_docente_permitido_agregar_y_asistencia(self):
        """Docente mantiene permisos para agregar alumnos y cargar asistencias."""
        url_agregar = reverse('alumnos:agregar_alumno', kwargs={'sala_id': self.sala.id})
        response_agregar = self.client_docente.get(url_agregar)
        self.assertEqual(response_agregar.status_code, 200)

        url_asistencia = reverse('alumnos:cargar_asistencia', kwargs={'sala_id': self.sala.id})
        response_asistencia = self.client_docente.get(url_asistencia)
        self.assertEqual(response_asistencia.status_code, 200)
