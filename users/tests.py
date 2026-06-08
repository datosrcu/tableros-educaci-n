from django.test import TestCase, Client
from django.urls import reverse
from users.models import Usuario
from jardines.models import Jardin, Programa, Subprograma, Sala

class CoorReportAndFormTests(TestCase):
    def setUp(self):
        # Create coordinator and programs
        self.coordinador = Usuario.objects.create_user(
            username='coord_test',
            password='password123',
            rol='coordinador'
        )
        self.prog1 = Programa.objects.create(nombre="Programa de Prueba 1")
        self.prog2 = Programa.objects.create(nombre="Programa de Prueba 2")
        
        # Associate prog1 with coordinator
        self.coordinador.programas_asignados.add(self.prog1)
        
        # Create gardens
        self.jardin1 = Jardin.objects.create(
            nombre="Jardin Prog 1",
            programa=self.prog1,
            direccion="Direccion 1",
            sector="Centro"
        )
        self.jardin2 = Jardin.objects.create(
            nombre="Jardin Prog 2",
            programa=self.prog2,
            direccion="Direccion 2",
            sector="Centro"
        )
        
        # Create client
        self.client = Client()
        self.client.login(username='coord_test', password='password123')

    def test_reporte_asistencia_mensual_filtering_for_coordinator(self):
        url = reverse('users:reporte_asistencia_mensual')
        
        # Default view: should only show gardens from assigned programs (jardin1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.jardin1.nombre)
        self.assertNotContains(response, self.jardin2.nombre)
        
        # Filtered by prog1 (assigned): should show jardin1
        response = self.client.get(f"{url}?programa={self.prog1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.jardin1.nombre)
        self.assertNotContains(response, self.jardin2.nombre)
        
        # Filtered by prog2 (unassigned): should NOT show jardin2 (since coordinator cannot see it)
        response = self.client.get(f"{url}?programa={self.prog2.id}")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.jardin2.nombre)

    def test_sala_form_validation_non_field_error(self):
        # Test that unique_sala_por_jardin_turno is validated and returned as a non-field error
        from users.forms import SalaForm
        
        # Create a Sala
        sala = Sala.objects.create(
            nombre="Sala Roja",
            jardin=self.jardin1,
            turno="mañana",
            horario_inicio="08:00",
            horario_fin="12:00"
        )
        
        # Try to validate a duplicate SalaForm
        data = {
            'jardin': self.jardin1.id,
            'nombre': 'Sala Roja', # same name
            'turno': 'mañana',
            'horario_inicio': '08:00',
            'horario_fin': '12:00',
            'docentes': [],
            'responsable': ''
        }
        
        form = SalaForm(data, user=self.coordinador)
        self.assertFalse(form.is_valid())
        # The unique constraint violation must be in non_field_errors
        self.assertTrue(len(form.non_field_errors()) > 0)
