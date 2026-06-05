from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from jardines.models import Programa, Jardin, Sala, AsistenciaDocente, inicializar_asistencia_diaria
from users.models import AccionAuditoria

User = get_user_model()

class AsistenciaDocenteTestCase(TestCase):
    def setUp(self):
        self.docente = User.objects.create_user(
            username="docentetested",
            password="testpassword",
            email="docentetested@example.com",
            rol="docente"
        )
        self.programa = Programa.objects.create(nombre="Test Programa", prefijo_comprobante="TP")
        self.jardin = Jardin.objects.create(
            nombre="Test Jardin",
            direccion="Test Direccion",
            sector="Centro",
            programa=self.programa
        )
        self.sala = Sala.objects.create(
            jardin=self.jardin,
            nombre="Test Sala",
            turno="mañana",
            horario_inicio="08:00",
            horario_fin="12:00"
        )
        # Asignar sala al docente
        self.sala.docentes.add(self.docente)
        self.client = Client()

    def test_inicializar_asistencia(self):
        # Inicializar asistencia diaria
        inicializar_asistencia_diaria(self.docente)
        
        # Verificar que se creó el registro para hoy
        hoy = timezone.now().date()
        asistencias = AsistenciaDocente.objects.filter(docente=self.docente, fecha=hoy)
        self.assertEqual(asistencias.count(), 1)
        
        asistencia = asistencias.first()
        self.assertFalse(asistencia.fichado)
        self.assertEqual(asistencia.estado, 'A')
        self.assertIsNone(asistencia.latitude)
        self.assertIsNone(asistencia.longitude)

    def test_registrar_asistencia_docente_success(self):
        self.client.login(username="docentetested", password="testpassword")
        
        # Inicializar la asistencia de hoy
        inicializar_asistencia_diaria(self.docente)
        
        post_data = {
            "latitude": "-35.123456",
            "longitude": "-65.654321"
        }
        
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        
        # Verificar que el registro se actualizó
        hoy = timezone.now().date()
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertTrue(asistencia.fichado)
        self.assertEqual(asistencia.estado, 'P')
        self.assertEqual(asistencia.latitude, Decimal("-35.123456"))
        self.assertEqual(asistencia.longitude, Decimal("-65.654321"))
        self.assertIsNotNone(asistencia.hora_ingreso)
        
        # Verificar que se creó la auditoría
        audits = AccionAuditoria.objects.filter(usuario=self.docente, modelo="AsistenciaDocente")
        self.assertEqual(audits.count(), 1)
        self.assertIn("Registró asistencia docente", audits.first().descripcion)

    def test_registrar_asistencia_docente_missing_coords(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        
        # Enviar sin coordenadas
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("requeridas", response.json()["message"])

    def test_registrar_asistencia_docente_invalid_coords(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        
        # Enviar coordenadas inválidas
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "invalid",
            "longitude": "coords"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

