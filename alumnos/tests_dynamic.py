from django.test import TestCase, Client
from django.urls import reverse
from users.models import Usuario
from jardines.models import Programa, Jardin, Sala
from formularios.models import EstructuraFormulario, CampoFormulario, RespuestaFormulario
from alumnos.models import Alumno, FichaProgramaAlumno
from django.core.exceptions import ValidationError

class DynamicFormIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear usuario coordinador
        self.coordinador = Usuario.objects.create_user(
            username="coord", password="password", rol="coordinador"
        )
        # Crear usuario docente
        self.docente = Usuario.objects.create_user(
            username="docente", password="password", rol="docente"
        )
        
        # Estructura jerárquica
        self.programa = Programa.objects.create(nombre="Test Program", usa_formulario_ampliado=True)
        self.jardin = Jardin.objects.create(
            nombre="Test Jardin", 
            programa=self.programa,
            direccion="Test Address 123",
            sector="Norte"
        )
        self.sala = Sala.objects.create(
            nombre="Test Sala", 
            jardin=self.jardin,
            turno="mañana"
        )
        
        # Asignar sala al docente
        self.docente.salas_asignadas.add(self.sala)
        
        # Crear estructura de formulario dinámico
        self.estructura = EstructuraFormulario.objects.create(programa=self.programa)
        self.campo1 = CampoFormulario.objects.create(
            estructura=self.estructura,
            etiqueta="Social Score",
            nombre_interno="social_score",
            tipo="numero",
            obligatorio=True,
            orden=1
        )
        self.campo2 = CampoFormulario.objects.create(
            estructura=self.estructura,
            etiqueta="Notes",
            nombre_interno="notes",
            tipo="texto",
            obligatorio=False,
            orden=2
        )

    def test_agregar_alumno_with_dynamic_form(self):
        self.client.login(username="docente", password="password")
        url = reverse("alumnos:agregar_alumno", kwargs={"sala_id": self.sala.id})
        
        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678",
            "fecha_nacimiento": "2015-01-01",
            "social_score": 100,
            "notes": "Test note"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        alumno = Alumno.objects.get(dni="12345678")
        self.assertEqual(alumno.nombre, "Juan")
        
        # Verificar que se creó la respuesta dinámica
        respuesta = RespuestaFormulario.objects.get(alumno=alumno)
        self.assertEqual(respuesta.datos["social_score"], 100)
        self.assertEqual(respuesta.datos["notes"], "Test note")

    def test_editar_alumno_with_dynamic_form(self):
        # Crear alumno primero
        alumno = Alumno.objects.create(
            nombre="Maria", 
            apellido="Gomez", 
            dni="87654321", 
            fecha_nacimiento="2016-05-05"
        )
        from alumnos.models import AsignacionSala
        AsignacionSala.objects.create(alumno=alumno, sala=self.sala, activo=True)
        FichaProgramaAlumno.objects.create(alumno=alumno)
        RespuestaFormulario.objects.create(
            alumno=alumno, 
            formulario=self.estructura, 
            datos={"social_score": 50, "notes": "Old note"}
        )
        
        self.client.login(username="docente", password="password")
        url = reverse("alumnos:editar_alumno", kwargs={"alumno_id": alumno.id})
        
        data = {
            "nombre": "Maria Updated",
            "apellido": "Gomez",
            "dni": "87654321",
            "fecha_nacimiento": "2016-05-05",
            "social_score": 80,
            "notes": "Updated note"
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        alumno.refresh_from_db()
        self.assertEqual(alumno.nombre, "Maria Updated")
        
        # Verificar actualización de respuesta dinámica
        respuesta = RespuestaFormulario.objects.get(alumno=alumno)
        self.assertEqual(respuesta.datos["social_score"], 80)
        self.assertEqual(respuesta.datos["notes"], "Updated note")

    def test_usuario_telefono_field(self):
        user = Usuario.objects.create_user(
            username="testuser_tel", 
            password="password", 
            telefono="1122334455"
        )
        self.assertEqual(user.telefono, "1122334455")
        
    def test_jardin_telefono_field(self):
        jardin = Jardin.objects.create(
            nombre="Jardin Tel", 
            programa=self.programa,
            direccion="Calle 123",
            sector="Norte",
            telefono="5544332211"
        )
        self.assertEqual(jardin.telefono, "5544332211")
