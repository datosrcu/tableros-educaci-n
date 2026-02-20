from django.test import TestCase
from jardines.models import Programa, Subprograma, Jardin, Sala
from alumnos.models import Inscripcion, Alumno  # Inscripcion might need Alumno context if linked? No, Inscripcion is standalone model.
from .models import EstructuraFormulario, CampoFormulario, RespuestaFormulario
from .forms import FormularioDinamico
from datetime import date

class FormularioDinamicoTests(TestCase):
    def setUp(self):
        # Setup basic hierarchy
        self.programa = Programa.objects.create(nombre="Programa Test", activo=True)
        self.subprograma = Subprograma.objects.create(programa=self.programa, nombre="Subprograma Test")
        self.jardin = Jardin.objects.create(
            programa=self.programa, 
            subprograma=self.subprograma,
            nombre="Jardin Test",
            direccion="Calle Falsa 123",
            sector="Norte"
        )
        # Sala requires jardin, nombre, turno
        self.sala = Sala.objects.create(
            jardin=self.jardin,
            nombre="Sala Roja",
            turno="mañana"
        )
        
        # Create Inscripcion
        self.inscripcion = Inscripcion.objects.create(
            programa=self.programa,
            subprograma=self.subprograma,
            espacio=self.jardin,
            sala=self.sala,
            apellido="Perez",
            nombre="Juan",
            dni="12345678",
            fecha_nacimiento=date(2020, 1, 1)
        )

        # Create EstructuraFormulario
        self.estructura = EstructuraFormulario.objects.create(programa=self.programa)

        # Create Campos
        self.campo_texto = CampoFormulario.objects.create(
            estructura=self.estructura,
            etiqueta="¿Color favorito?",
            nombre_interno="color_favorito",
            tipo="texto",
            orden=1
        )
        self.campo_numero = CampoFormulario.objects.create(
            estructura=self.estructura,
            etiqueta="Cantidad de hermanos",
            nombre_interno="cant_hermanos",
            tipo="numero",
            orden=2
        )
        self.campo_select = CampoFormulario.objects.create(
            estructura=self.estructura,
            etiqueta="Transporte",
            nombre_interno="transporte",
            tipo="select",
            opciones="Auto,Bus,Caminando",
            orden=3
        )

    def test_formulario_dinamico_generation(self):
        """Test that the form generates fields correctly based on structure."""
        form = FormularioDinamico(estructura=self.estructura)
        
        self.assertIn("color_favorito", form.fields)
        self.assertIn("cant_hermanos", form.fields)
        self.assertIn("transporte", form.fields)
        
        # Check select choices
        choices = [c[0] for c in form.fields["transporte"].choices]
        self.assertIn("Auto", choices)
        self.assertIn("Bus", choices)

    def test_respuesta_guardado(self):
        """Test saving a response."""
        data = {
            "color_favorito": "Azul",
            "cant_hermanos": 2,
            "transporte": "Bus"
        }
        
        form = FormularioDinamico(data, estructura=self.estructura)
        self.assertTrue(form.is_valid())
        
        respuesta = RespuestaFormulario.objects.create(
            inscripcion=self.inscripcion,
            formulario=self.estructura,
            datos=form.cleaned_data
        )
        
        self.assertEqual(respuesta.datos["color_favorito"], "Azul")
        self.assertEqual(respuesta.datos["cant_hermanos"], 2)

    def test_formulario_invalido(self):
        """Test required fields."""
        self.campo_texto.obligatorio = True
        self.campo_texto.save()
        
        data = {
            "cant_hermanos": 2,  # Missing color_favorito
        }
        form = FormularioDinamico(data, estructura=self.estructura)
        self.assertFalse(form.is_valid())
        self.assertIn("color_favorito", form.errors)
