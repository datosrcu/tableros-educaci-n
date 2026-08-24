from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import time, date, timedelta

from jardines.models import (
    Programa, Jardin, Sala, AsistenciaDocente,
    TipoActividadEspecial, ActividadEspecial, inicializar_asistencia_diaria
)

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class ActividadesEspecialesTestCase(TestCase):
    def setUp(self):
        # Crear usuarios con diferentes roles
        self.admin = User.objects.create_superuser(
            username="admin_test",
            password="adminpassword",
            email="admin@test.com",
            rol="administrador"
        )
        self.coordinador = User.objects.create_user(
            username="coord_test",
            password="coordpassword",
            email="coord@test.com",
            rol="coordinador"
        )
        self.docente = User.objects.create_user(
            username="docente_test",
            password="docentepassword",
            email="docente@test.com",
            first_name="María",
            last_name="García",
            rol="docente"
        )
        self.docente2 = User.objects.create_user(
            username="docente2_test",
            password="docente2password",
            email="docente2@test.com",
            first_name="Juan",
            last_name="Pérez",
            rol="docente"
        )

        # Estructura educativa
        self.programa = Programa.objects.create(nombre="Programa Maternal", prefijo_comprobante="PM")
        self.coordinador.programas_asignados.add(self.programa)

        self.jardin = Jardin.objects.create(
            nombre="Jardín Central",
            direccion="Calle Falsa 123",
            sector="Centro",
            programa=self.programa
        )

        # Sala Mañana: 10:00 a 11:00 hs
        self.sala_manana = Sala.objects.create(
            jardin=self.jardin,
            nombre="Sala Amarilla",
            turno="mañana",
            horario_inicio=time(10, 0),
            horario_fin=time(11, 0)
        )
        self.sala_manana.docentes.add(self.docente)

        # Sala Tarde: 18:00 a 20:00 hs
        self.sala_tarde = Sala.objects.create(
            jardin=self.jardin,
            nombre="Sala Azul",
            turno="tarde",
            horario_inicio=time(18, 0),
            horario_fin=time(20, 0)
        )
        self.sala_tarde.docentes.add(self.docente2)

        # Tipo de actividad default
        self.tipo_festejo, _ = TipoActividadEspecial.objects.get_or_create(
            nombre="Festejos / Eventos Institucionales",
            defaults={"es_default": True, "activo": True}
        )
        self.tipo_capacitacion, _ = TipoActividadEspecial.objects.get_or_create(
            nombre="Capacitaciones",
            defaults={"es_default": True, "activo": True}
        )

        self.client = Client()

    def test_docente_no_tiene_permiso_para_gestionar_actividades(self):
        """Un usuario docente no tiene permisos para crear, listar o editar actividades."""
        self.client.login(username="docente_test", password="docentepassword")

        # Intentar acceder a la lista
        resp_lista = self.client.get(reverse("jardines:lista_actividades"))
        self.assertEqual(resp_lista.status_code, 403)

        # Intentar crear
        resp_crear = self.client.get(reverse("jardines:crear_actividad"))
        self.assertEqual(resp_crear.status_code, 403)

    def test_coordinador_y_admin_tienen_permisos(self):
        """Coordinadores y administradores pueden acceder al módulo."""
        # Coordinador
        self.client.login(username="coord_test", password="coordpassword")
        resp_coord = self.client.get(reverse("jardines:lista_actividades"))
        self.assertEqual(resp_coord.status_code, 200)

        # Admin
        self.client.login(username="admin_test", password="adminpassword")
        resp_admin = self.client.get(reverse("jardines:lista_actividades"))
        self.assertEqual(resp_admin.status_code, 200)

    def test_creacion_tipo_actividad_ajax(self):
        """Se puede crear un tipo personalizado de actividad en el momento vía AJAX."""
        self.client.login(username="coord_test", password="coordpassword")
        post_data = {
            "nombre": "Taller Comunitario Especial",
            "descripcion": "Taller barrial y pedagógico"
        }
        resp = self.client.post(reverse("jardines:crear_tipo_actividad_ajax"), post_data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["nombre"], "Taller Comunitario Especial")
        self.assertTrue(TipoActividadEspecial.objects.filter(nombre="Taller Comunitario Especial").exists())

    def test_crear_actividad_especial_por_alcance_docente(self):
        """Crear una actividad puntual para un docente."""
        self.client.login(username="coord_test", password="coordpassword")
        hoy = timezone.localtime(timezone.now()).date()

        post_data = {
            "nombre": "Festejo Día de las Infancias",
            "tipo": self.tipo_festejo.id,
            "fecha": hoy.strftime("%Y-%m-%d"),
            "hora_inicio": "12:00",
            "hora_fin": "14:00",
            "turno_afectado": "todo_el_dia",
            "descripcion": "Festejo general en turno tarde",
            "alcance": "docente",
            "docentes": [self.docente.id]
        }
        resp = self.client.post(reverse("jardines:crear_actividad"), post_data)
        self.assertEqual(resp.status_code, 302)

        actividad = ActividadEspecial.objects.get(nombre="Festejo Día de las Infancias")
        self.assertTrue(actividad.afecta_docente(self.docente))
        self.assertFalse(actividad.afecta_docente(self.docente2))

    def test_exencion_de_clase_por_evento_en_horario_distinto(self):
        """
        Docente tiene clase de 10:00 a 11:00 hs y actividad de 12:00 a 14:00 hs el mismo día.
        No debe figurar como 'Ausente' (A), sino como Exento (E).
        """
        hoy = timezone.localtime(timezone.now()).date()

        # Crear actividad para el docente de 12 a 14 hs
        actividad = ActividadEspecial.objects.create(
            nombre="Capacitación Pedagógica",
            tipo=self.tipo_capacitacion,
            fecha=hoy,
            hora_inicio=time(12, 0),
            hora_fin=time(14, 0),
            alcance="docente",
            creado_por=self.coordinador
        )
        actividad.docentes.add(self.docente)

        # Inicializar asistencia diaria del docente
        inicializar_asistencia_diaria(self.docente)

        # Verificar el registro de asistencia generado
        asistencia = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy)
        self.assertEqual(asistencia.estado, 'E')
        self.assertNotEqual(asistencia.estado, 'A')
        self.assertEqual(asistencia.estado_jornada, "Exento por Actividad Especial")
        self.assertIn("Capacitación Pedagógica", asistencia.observaciones)

    def test_solapamiento_parcial(self):
        """
        Docente2 tiene clase de 18:00 a 20:00 hs y actividad de 19:00 a 20:00 hs.
        Ficha al inicio (18:00 hs) y queda exento del tramo restante.
        """
        hoy = timezone.localtime(timezone.now()).date()

        actividad = ActividadEspecial.objects.create(
            nombre="Reunión Institucional",
            tipo=self.tipo_capacitacion,
            fecha=hoy,
            hora_inicio=time(19, 0),
            hora_fin=time(20, 0),
            alcance="sala",
            creado_por=self.coordinador
        )
        actividad.salas.add(self.sala_tarde)

        # Inicializar asistencia diaria
        inicializar_asistencia_diaria(self.docente2)

        # El estado inicial permite fichar al inicio
        asistencia = AsistenciaDocente.objects.get(docente=self.docente2, fecha=hoy)
        self.assertIn("solapamiento", asistencia.observaciones.lower())

        # Docente ficha ingreso a las 18 hs
        self.client.login(username="docente2_test", password="docente2password")
        post_fichaje = {
            "asistencia_id": asistencia.id,
            "jardin_id": self.jardin.id,
            "turno": "tarde",
            "latitude": "-35.123456",
            "longitude": "-65.654321",
            "tipo": "ingreso"
        }
        resp = self.client.post(reverse("jardines:registrar_asistencia_docente"), post_fichaje)
        self.assertEqual(resp.status_code, 200)

        asistencia.refresh_from_db()
        self.assertTrue(asistencia.fichado)
        self.assertEqual(asistencia.estado, 'P')

    def test_banner_en_portal_docente(self):
        """El portal docente detalla claramente la actividad asignada."""
        hoy = timezone.localtime(timezone.now()).date()

        actividad = ActividadEspecial.objects.create(
            nombre="Festejo Día de las Infancias",
            tipo=self.tipo_festejo,
            fecha=hoy,
            hora_inicio=time(12, 0),
            hora_fin=time(14, 0),
            turno_afectado="todo_el_dia",
            alcance="docente",
            descripcion="Presentarse en el SUM municipal",
            creado_por=self.coordinador
        )
        actividad.docentes.add(self.docente)

        self.client.login(username="docente_test", password="docentepassword")
        resp = self.client.get(reverse("alumnos:dashboard_docente"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Festejo Día de las Infancias")
        self.assertContains(resp, "Exención Activa")
        self.assertContains(resp, "Exento por Actividad")

    def test_turno_afectado_diferenciacion(self):
        """
        Un docente asignado tanto a sala de turno mañana como a sala de turno tarde:
        - Si la actividad es de 11:00 a 11:30 hs con turno_afectado='mañana',
          únicamente la clase de turno mañana queda exenta ('E').
          La clase de turno tarde permanece obligatoria ('A').
        """
        hoy = timezone.localtime(timezone.now()).date()
        # Asignar a docente a ambas salas (mañana y tarde)
        self.sala_tarde.docentes.add(self.docente)

        # Crear actividad solo para turno mañana
        actividad_manana = ActividadEspecial.objects.create(
            nombre="Reunión Corta Mañana",
            tipo=self.tipo_capacitacion,
            fecha=hoy,
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
            turno_afectado="mañana",
            alcance="docente",
            creado_por=self.coordinador
        )
        actividad_manana.docentes.add(self.docente)

        # Inicializar asistencia
        inicializar_asistencia_diaria(self.docente)

        asist_manana = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy, turno="mañana")
        asist_tarde = AsistenciaDocente.objects.get(docente=self.docente, fecha=hoy, turno="tarde")

        # Turno mañana queda exento
        self.assertEqual(asist_manana.estado, 'E')
        self.assertEqual(asist_manana.estado_jornada, "Exento por Actividad Especial")

        # Turno tarde NO queda exento
        self.assertEqual(asist_tarde.estado, 'A')
        self.assertNotEqual(asist_tarde.estado, 'E')

