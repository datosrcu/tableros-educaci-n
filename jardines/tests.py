from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from jardines.models import Programa, Jardin, Sala, AsistenciaDocente, inicializar_asistencia_diaria
from users.models import AccionAuditoria

User = get_user_model()

@override_settings(SECURE_SSL_REDIRECT=False)
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
        inicializar_asistencia_diaria(self.docente)
        hoy = timezone.now().date()
        asistencias = AsistenciaDocente.objects.filter(docente=self.docente, fecha=hoy)
        self.assertEqual(asistencias.count(), 1)
        asistencia = asistencias.first()
        self.assertFalse(asistencia.fichado)
        self.assertEqual(asistencia.estado, 'A')
        self.assertIsNone(asistencia.latitude)
        self.assertIsNone(asistencia.longitude)
        # Nuevos campos deben inicializarse vacíos
        self.assertFalse(asistencia.fichado_salida)
        self.assertIsNone(asistencia.hora_salida)

    def test_registrar_asistencia_docente_success(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        post_data = {
            "latitude": "-35.123456",
            "longitude": "-65.654321",
            "tipo": "ingreso"
        }
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["tipo"], "ingreso")
        hoy = timezone.now().date()
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertTrue(asistencia.fichado)
        self.assertFalse(asistencia.fichado_salida)
        self.assertEqual(asistencia.estado, 'P')
        self.assertEqual(asistencia.latitude, Decimal("-35.123456"))
        self.assertEqual(asistencia.longitude, Decimal("-65.654321"))
        self.assertIsNotNone(asistencia.hora_ingreso)
        self.assertIsNone(asistencia.hora_salida)
        self.assertEqual(asistencia.estado_jornada, "Jornada en curso")
        # Verificar auditoría de ingreso
        audits = AccionAuditoria.objects.filter(usuario=self.docente, modelo="AsistenciaDocente")
        self.assertEqual(audits.count(), 1)
        self.assertIn("ingreso", audits.first().descripcion.lower())

    def test_registrar_asistencia_docente_missing_coords(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("requeridas", response.json()["message"])

    def test_registrar_asistencia_docente_invalid_coords(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "invalid",
            "longitude": "coords"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_registrar_asistencia_docente_high_precision_coords(self):
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        post_data = {
            "latitude": "-35.123456789012",
            "longitude": "-65.654321098765",
            "tipo": "ingreso"
        }
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        hoy = timezone.now().date()
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertTrue(asistencia.fichado)
        self.assertEqual(asistencia.latitude, Decimal("-35.123457"))
        self.assertEqual(asistencia.longitude, Decimal("-65.654321"))

    # ─────────────────────────────────────────────────────────
    # TESTS NUEVOS: Fichaje de Salida
    # ─────────────────────────────────────────────────────────

    def test_fichaje_salida_exitoso(self):
        """Flujo completo: ingreso → jornada en curso → salida → jornada finalizada."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        hoy = timezone.now().date()
        # Fichar ingreso
        resp_ingreso = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        self.assertEqual(resp_ingreso.status_code, 200)
        self.assertEqual(resp_ingreso.json()["tipo"], "ingreso")
        # Fichar salida
        resp_salida = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123500", "longitude": "-65.654400", "tipo": "salida"
        })
        self.assertEqual(resp_salida.status_code, 200)
        self.assertEqual(resp_salida.json()["status"], "success")
        self.assertEqual(resp_salida.json()["tipo"], "salida")
        self.assertIn("horas_trabajadas", resp_salida.json())
        # Verificar estado final
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertTrue(asistencia.fichado)
        self.assertTrue(asistencia.fichado_salida)
        self.assertIsNotNone(asistencia.hora_ingreso)
        self.assertIsNotNone(asistencia.hora_salida)
        self.assertEqual(asistencia.estado_jornada, "Jornada finalizada")
        self.assertEqual(asistencia.latitude_salida, Decimal("-35.123500"))
        self.assertEqual(asistencia.longitude_salida, Decimal("-65.654400"))
        # Verificar auditorías: ingreso + salida
        audits = AccionAuditoria.objects.filter(usuario=self.docente, modelo="AsistenciaDocente")
        self.assertEqual(audits.count(), 2)
        descripciones = [a.descripcion.lower() for a in audits]
        self.assertTrue(any("ingreso" in d for d in descripciones))
        self.assertTrue(any("salida" in d for d in descripciones))

    def test_fichaje_salida_sin_ingreso_previo(self):
        """No debe permitir fichar salida sin ingreso previo."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "salida"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["status"], "error")
        self.assertIn("ingreso", resp.json()["message"].lower())

    def test_doble_salida_bloqueada(self):
        """No debe permitir fichar salida dos veces en la misma jornada."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "salida"
        })
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "salida"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "already")

    def test_doble_ingreso_bloqueado(self):
        """No debe permitir fichar ingreso dos veces en la misma jornada."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "already")

    def test_fichaje_salida_coords_requeridas(self):
        """El fichaje de salida también debe exigir coordenadas GPS."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "tipo": "salida"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["status"], "error")
        self.assertIn("requeridas", resp.json()["message"])

    def test_estado_jornada_historico_sin_salida(self):
        """Registros históricos con ingreso pero sin salida deben mostrar 'Ingreso sin salida'."""
        from datetime import date, timedelta
        ayer = date.today() - timedelta(days=1)
        asistencia = AsistenciaDocente.objects.create(
            docente=self.docente,
            jardin=self.jardin,
            turno="mañana",
            fecha=ayer,
            fichado=True,
            fichado_salida=False,
            estado='P',
            hora_ingreso=timezone.localtime(timezone.now()).time()
        )
        self.assertEqual(asistencia.estado_jornada, "Ingreso sin salida")
        self.assertEqual(asistencia.horas_trabajadas_str, "Ingreso sin salida")

    def test_horas_trabajadas_calculo(self):
        """El cálculo de horas trabajadas debe ser correcto entre hora_ingreso y hora_salida."""
        from datetime import time
        asistencia = AsistenciaDocente.objects.create(
            docente=self.docente,
            jardin=self.jardin,
            turno="mañana",
            fecha=timezone.now().date(),
            fichado=True,
            fichado_salida=True,
            estado='P',
            hora_ingreso=time(8, 0),
            hora_salida=time(12, 30)
        )
        self.assertEqual(asistencia.horas_trabajadas_str, "04:30 hs")

    def test_auto_deteccion_tipo_ingreso(self):
        """Sin parámetro 'tipo', debe auto-detectar que corresponde fichar ingreso."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456",
            "longitude": "-65.654321"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertEqual(resp.json()["tipo"], "ingreso")

    def test_auto_deteccion_tipo_salida(self):
        """Sin parámetro 'tipo' y con ingreso ya fichado, debe auto-detectar salida."""
        self.client.login(username="docentetested", password="testpassword")
        inicializar_asistencia_diaria(self.docente)
        self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456", "longitude": "-65.654321", "tipo": "ingreso"
        })
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), {
            "latitude": "-35.123456",
            "longitude": "-65.654321"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertEqual(resp.json()["tipo"], "salida")

    def test_resumen_actividad_docente_coordinator(self):
        coordinador = User.objects.create_user(
            username="coordinadortest",
            password="testpassword",
            rol="coordinador"
        )
        coordinador.programas_asignados.add(self.programa)
        self.client.login(username="coordinadortest", password="testpassword")
        docente_sin_sala = User.objects.create_user(
            username="docentesinsala",
            password="testpassword",
            rol="docente"
        )
        hoy = timezone.localtime(timezone.now()).date()
        AsistenciaDocente.objects.create(
            docente=docente_sin_sala,
            jardin=self.jardin,
            fecha=hoy,
            fichado=True,
            hora_ingreso=timezone.localtime(timezone.now()).time()
        )
        response = self.client.get(reverse("jardines:resumen_actividad_docente"))
        self.assertEqual(response.status_code, 200)
        resumen = response.context["resumen"]
        docentes_en_resumen = [item["docente"] for item in resumen]
        self.assertIn(self.docente, docentes_en_resumen)
        self.assertIn(docente_sin_sala, docentes_en_resumen)
        # Verificar que los nuevos campos están en el contexto del resumen
        for item in resumen:
            self.assertIn("fichado_salida", item)
            self.assertIn("horas_trabajadas", item)

    def test_inicializar_asistencia_diaria_does_not_overwrite(self):
        inicializar_asistencia_diaria(self.docente)
        hoy = timezone.now().date()
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        asistencia.fichado = True
        asistencia.fichado_salida = True
        asistencia.estado = 'P'
        asistencia.save()
        inicializar_asistencia_diaria(self.docente)
        asistencia_despues = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertTrue(asistencia_despues.fichado)
        self.assertTrue(asistencia_despues.fichado_salida)
        self.assertEqual(asistencia_despues.estado, 'P')

    def test_registrar_asistencia_onthefly(self):
        self.sala_tarde = Sala.objects.create(
            jardin=self.jardin,
            nombre="Taller Tarde",
            turno="tarde",
            horario_inicio="14:00",
            horario_fin="18:00"
        )
        self.sala_tarde.docentes.add(self.docente)
        self.client.login(username="docentetested", password="testpassword")
        post_data = {
            "latitude": "-35.123456",
            "longitude": "-65.654321",
            "jardin_id": self.jardin.id,
            "turno": "tarde",
            "tipo": "ingreso"
        }
        response = self.client.post(reverse("jardines:registrar_asistencia_docente"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        hoy = timezone.now().date()
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, jardin=self.jardin, turno="tarde", fecha=hoy)
        self.assertTrue(asistencia.fichado)
        self.assertFalse(asistencia.fichado_salida)
        self.assertEqual(asistencia.estado, 'P')

    def test_auxiliar_con_salas_dashboard(self):
        auxiliar = User.objects.create_user(
            username="auxiliartested",
            password="testpassword",
            rol="auxiliar"
        )
        self.sala.docentes.add(auxiliar)
        self.client.login(username="auxiliartested", password="testpassword")
        response = self.client.get(reverse("alumnos:dashboard_docente"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["turnos_hoy"]), 1)
        self.assertEqual(response.context["turnos_hoy"][0]["jardin_id"], self.jardin.id)
        turno_item = response.context["turnos_hoy"][0]
        self.assertIn("fichado_salida", turno_item)
        self.assertIn("estado_jornada", turno_item)
        self.assertIn("horas_trabajadas", turno_item)
