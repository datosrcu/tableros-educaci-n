from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date

from jardines.models import Programa, Subprograma, Jardin, Sala
from alumnos.models import Alumno, AsignacionSala
from .models import ProgramaCobro, ResponsableCobro, Pago

User = get_user_model()

class CobrosTestCase(TestCase):
    def setUp(self):
        # 1. Crear superusuario, coordinador y docente no autorizado
        self.superuser = User.objects.create_superuser(
            username="admin",
            password="adminpassword",
            email="admin@example.com",
            rol="administrador"
        )
        self.coordinator = User.objects.create_user(
            username="coordinador1",
            password="coordpassword",
            email="coord@example.com",
            rol="coordinador"
        )
        self.unauthorized_user = User.objects.create_user(
            username="docente1",
            password="docentepassword",
            email="docente@example.com",
            rol="docente"
        )

        # 2. Crear programas
        self.programa_arte = Programa.objects.create(nombre="Escuela de Arte", activo=True)
        self.programa_carpinteria = Programa.objects.create(nombre="Carpintería", activo=True)

        # 3. Configurar cobros para programas
        self.pc_arte = ProgramaCobro.objects.create(
            programa=self.programa_arte,
            importe_mensual=Decimal("15000.00"),
            activo=True
        )
        self.pc_carp = ProgramaCobro.objects.create(
            programa=self.programa_carpinteria,
            importe_mensual=Decimal("20000.00"),
            activo=True
        )

        # 4. Asignar coordinador como responsable de cobros de Escuela de Arte
        self.responsabilidad = ResponsableCobro.objects.create(
            usuario=self.coordinator,
            programa=self.programa_arte,
            rol="titular"
        )

        # 5. Crear espacios (Jardines)
        self.jardin_arte = Jardin.objects.create(
            nombre="Centro Cultural Norte",
            direccion="Calle 123",
            sector="Centro",
            programa=self.programa_arte
        )
        self.jardin_carp = Jardin.objects.create(
            nombre="Taller Carpintería Sur",
            direccion="Calle 456",
            sector="Centro",
            programa=self.programa_carpinteria
        )

        # 6. Crear Salas
        self.sala_arte = Sala.objects.create(
            jardin=self.jardin_arte,
            nombre="Sala Pintura Mañana",
            turno="mañana",
            horario_inicio="08:00",
            horario_fin="12:00"
        )
        self.sala_carp = Sala.objects.create(
            jardin=self.jardin_carp,
            nombre="Sala Madera Tarde",
            turno="tarde",
            horario_inicio="14:00",
            horario_fin="17:00"
        )

        # 7. Crear Alumnos
        self.alumno_arte = Alumno.objects.create(
            nombre="Juan",
            apellido="Perez",
            dni="40123456",
            fecha_nacimiento="2012-05-15"
        )
        self.alumno_carp = Alumno.objects.create(
            nombre="Maria",
            apellido="Gomez",
            dni="41123456",
            fecha_nacimiento="2011-08-20"
        )

        # 8. Asignar Alumnos a Salas
        self.asignacion_arte = AsignacionSala.objects.create(
            alumno=self.alumno_arte,
            sala=self.sala_arte,
            activo=True
        )
        self.asignacion_carp = AsignacionSala.objects.create(
            alumno=self.alumno_carp,
            sala=self.sala_carp,
            activo=True
        )

        self.client = Client()

    def test_permission_denied_for_unauthorized_users(self):
        # Login como docente (sin permisos de cobro)
        self.client.login(username="docente1", password="docentepassword")
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_permission_granted_for_superusers_and_responsables(self):
        # Superusuario
        self.client.login(username="admin", password="adminpassword")
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.status_code, 200)
        
        # Coordinador responsable de Arte
        self.client.login(username="coordinador1", password="coordpassword")
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_scoped_data(self):
        # Login como coordinador (solo tiene permisos para Escuela de Arte)
        self.client.login(username="coordinador1", password="coordpassword")
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.status_code, 200)
        
        # Debe visualizar al alumno de Arte pero no al de Carpintería
        rows = response.context["rows"]
        alumnos_list = [r["alumno"] for r in rows]
        self.assertIn(self.alumno_arte, alumnos_list)
        self.assertNotIn(self.alumno_carp, alumnos_list)

        # Verificar indicadores del dashboard para su alcance
        self.assertEqual(response.context["total_alumnos"], 1)
        self.assertEqual(response.context["total_adeudan"], 1)
        self.assertEqual(response.context["total_pagados"], 0)

    def test_superuser_dashboard_views_all(self):
        # Login como superusuario (ve todo)
        self.client.login(username="admin", password="adminpassword")
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.status_code, 200)
        
        rows = response.context["rows"]
        self.assertEqual(len(rows), 2)
        alumnos_list = [r["alumno"] for r in rows]
        self.assertIn(self.alumno_arte, alumnos_list)
        self.assertIn(self.alumno_carp, alumnos_list)

    def test_register_payment(self):
        self.client.login(username="coordinador1", password="coordpassword")
        
        # Cargar pago para el alumno de Arte para el mes actual
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        post_data = {
            "alumno": self.alumno_arte.id,
            "programa": self.programa_arte.id,
            "importe": "15000.00",
            "fecha_pago": timezone.now().date().strftime("%Y-%m-%d"),
            "metodo_pago": "transferencia",
            "estado": "pagado",
            "mes_pagado": current_month,
            "anio_pagado": current_year,
            "observaciones": "Pago de prueba cuota de arte"
        }
        response = self.client.post(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]), post_data)
        self.assertRedirects(response, reverse("cobros:dashboard"))
        
        # Verificar que el pago se haya guardado
        pago = Pago.objects.filter(alumno=self.alumno_arte, programa=self.programa_arte).first()
        self.assertIsNotNone(pago)
        self.assertEqual(pago.importe, Decimal("15000.00"))
        self.assertEqual(pago.registrado_por, self.coordinator)
        self.assertEqual(pago.mes_pagado, current_month)
        self.assertEqual(pago.anio_pagado, current_year)
        
        # Verificar que el dashboard actualice los indicadores
        response = self.client.get(reverse("cobros:dashboard"))
        self.assertEqual(response.context["total_pagados"], 1)
        self.assertEqual(response.context["total_adeudan"], 0)
        self.assertEqual(response.context["recaudacion_mes"], Decimal("15000.00"))

    def test_historial_pagos(self):
        # Registrar un pago previo
        Pago.objects.create(
            alumno=self.alumno_arte,
            programa=self.programa_arte,
            importe=Decimal("15000.00"),
            fecha_pago=timezone.now().date(),
            metodo_pago="efectivo",
            estado="pagado",
            registrado_por=self.coordinator,
            mes_pagado=5,
            anio_pagado=2026
        )

        self.client.login(username="coordinador1", password="coordpassword")
        response = self.client.get(reverse("cobros:historial_pagos", args=[self.alumno_arte.id]))
        self.assertEqual(response.status_code, 200)
        pagos = response.context["pagos"]
        self.assertEqual(len(pagos), 1)
        self.assertEqual(pagos[0].importe, Decimal("15000.00"))

    def test_historical_debt_calculation(self):
        from unittest.mock import patch
        from datetime import datetime
        # Forzar fecha de ingreso en Abril 2026
        AsignacionSala.objects.filter(id=self.asignacion_arte.id).update(
            fecha_ingreso=date(2026, 4, 15)
        )
        self.asignacion_arte.refresh_from_db()
        
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2026, 6, 15, 12, 0, 0))

            # Consultar Junio 2026
            self.client.login(username="coordinador1", password="coordpassword")
            response = self.client.get(reverse("cobros:dashboard") + "?mes=6&anio=2026")
            self.assertEqual(response.status_code, 200)
            
            rows = response.context["rows"]
            row_arte = next(r for r in rows if r["alumno"] == self.alumno_arte)
            
            # Debe adeudar Abril, Mayo y Junio
            self.assertEqual(len(row_arte["meses_adeudados_list"]), 3)
            self.assertIn("Abril 2026", row_arte["meses_adeudados_list"])
            self.assertIn("Mayo 2026", row_arte["meses_adeudados_list"])
            self.assertIn("Junio 2026", row_arte["meses_adeudados_list"])
        
            # Verificar que el formulario de pago preselecciona el mes más antiguo (Abril = 4)
            response_form = self.client.get(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]))
            self.assertEqual(response_form.status_code, 200)
            form = response_form.context["form"]
            self.assertEqual(form.initial["mes_pagado"], 4)
            self.assertEqual(form.initial["anio_pagado"], 2026)

    def test_descargar_comprobante_success(self):
        # Crear un pago
        pago = Pago.objects.create(
            alumno=self.alumno_arte,
            programa=self.programa_arte,
            importe=Decimal("15000.00"),
            fecha_pago=timezone.now().date(),
            metodo_pago="transferencia",
            estado="pagado",
            registrado_por=self.coordinator,
            mes_pagado=6,
            anio_pagado=2026
        )
        
        self.client.login(username="coordinador1", password="coordpassword")
        response = self.client.get(reverse("cobros:descargar_comprobante", args=[pago.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f"attachment; filename=\"Bono_Contribucion_{pago.numero_comprobante}.pdf\"", response['Content-Disposition'])
        # El contenido de un PDF válido empieza por %PDF
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_descargar_comprobante_unauthorized(self):
        pago = Pago.objects.create(
            alumno=self.alumno_arte,
            programa=self.programa_arte,
            importe=Decimal("15000.00"),
            fecha_pago=timezone.now().date(),
            metodo_pago="transferencia",
            estado="pagado",
            registrado_por=self.coordinator,
            mes_pagado=6,
            anio_pagado=2026
        )
        
        # Docente no tiene permisos
        self.client.login(username="docente1", password="docentepassword")
        response = self.client.get(reverse("cobros:descargar_comprobante", args=[pago.id]))
        self.assertEqual(response.status_code, 403)

    def test_descargar_comprobante_different_coordinator(self):
        # Pago del programa de Carpintería
        pago_carp = Pago.objects.create(
            alumno=self.alumno_carp,
            programa=self.programa_carpinteria,
            importe=Decimal("20000.00"),
            fecha_pago=timezone.now().date(),
            metodo_pago="transferencia",
            estado="pagado",
            registrado_por=self.superuser,
            mes_pagado=6,
            anio_pagado=2026
        )
        
        # Coordinador1 solo tiene permisos para Escuela de Arte, no Carpintería
        self.client.login(username="coordinador1", password="coordpassword")
        response = self.client.get(reverse("cobros:descargar_comprobante", args=[pago_carp.id]))
        self.assertEqual(response.status_code, 403)

    def test_registrar_pago_con_envio_correo(self):
        # Configurar correo inicial
        self.alumno_arte.email = "original@example.com"
        self.alumno_arte.save()
        
        self.client.login(username="coordinador1", password="coordpassword")
        
        # Cargar formulario y verificar precompletado
        response_get = self.client.get(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context["form"].initial["correo_envio"], "original@example.com")
        
        # Guardar pago con nuevo correo
        post_data = {
            "alumno": self.alumno_arte.id,
            "programa": self.programa_arte.id,
            "importe": "15000.00",
            "fecha_pago": timezone.now().date().strftime("%Y-%m-%d"),
            "metodo_pago": "transferencia",
            "estado": "pagado",
            "mes_pagado": 6,
            "anio_pagado": 2026,
            "enviar_correo": True,
            "correo_envio": "nuevo@example.com",
            "observaciones": ""
        }
        response_post = self.client.post(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]), post_data)
        self.assertRedirects(response_post, reverse("cobros:dashboard"))
        
        # Verificar pago guardado y email actualizado del alumno
        pago = Pago.objects.filter(alumno=self.alumno_arte, mes_pagado=6, anio_pagado=2026).first()
        self.assertIsNotNone(pago)
        self.assertTrue(pago.enviar_correo)
        self.assertEqual(pago.correo_envio, "nuevo@example.com")
        
        self.alumno_arte.refresh_from_db()
        self.assertEqual(self.alumno_arte.email, "nuevo@example.com")

    def test_registrar_pago_validation_missing_correo(self):
        self.client.login(username="coordinador1", password="coordpassword")
        
        post_data = {
            "alumno": self.alumno_arte.id,
            "programa": self.programa_arte.id,
            "importe": "15000.00",
            "fecha_pago": timezone.now().date().strftime("%Y-%m-%d"),
            "metodo_pago": "transferencia",
            "estado": "pagado",
            "mes_pagado": 6,
            "anio_pagado": 2026,
            "enviar_correo": True,
            "correo_envio": "",  # Enviar correo en True pero correo_envio vacío
            "observaciones": ""
        }
        response_post = self.client.post(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]), post_data)
        self.assertEqual(response_post.status_code, 200) # Recarga la página por error
        form = response_post.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("correo_envio", form.errors)
        self.assertEqual(form.errors["correo_envio"], ["Debe ingresar un correo electrónico si activa la opción de envío."])

    def test_registrar_pago_duplicate_period(self):
        # 1. Registrar un primer pago para Junio de 2026
        Pago.objects.create(
            alumno=self.alumno_arte,
            programa=self.programa_arte,
            importe=Decimal("15000.00"),
            fecha_pago=timezone.now().date(),
            metodo_pago="efectivo",
            estado="pagado",
            registrado_por=self.coordinator,
            mes_pagado=6,
            anio_pagado=2026
        )
        
        self.client.login(username="coordinador1", password="coordpassword")
        
        # 2. Intentar registrar otro pago para el mismo alumno, programa y período
        post_data = {
            "alumno": self.alumno_arte.id,
            "programa": self.programa_arte.id,
            "importe": "15000.00",
            "fecha_pago": timezone.now().date().strftime("%Y-%m-%d"),
            "metodo_pago": "transferencia",
            "estado": "pagado",
            "mes_pagado": 6,
            "anio_pagado": 2026,
            "enviar_correo": False,
            "observaciones": ""
        }
        
        response = self.client.post(reverse("cobros:registrar_pago", args=[self.asignacion_arte.id]), post_data)
        # Debe fallar y recargar la página con error de validación en lugar de redirigir
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("mes_pagado", form.errors)
        self.assertEqual(form.errors["mes_pagado"], ["Ya existe un pago registrado como 'Pagado' para este alumno en el período seleccionado."])

    def test_dashboard_espacio_filter(self):
        # Iniciar sesión como administrador (ve todos los programas y espacios)
        self.client.login(username="admin", password="adminpassword")
        
        # Filtrar por el jardín de Arte
        response = self.client.get(reverse("cobros:dashboard") + f"?espacio={self.jardin_arte.id}")
        self.assertEqual(response.status_code, 200)
        
        rows = response.context["rows"]
        alumnos_list = [r["alumno"] for r in rows]
        # Debe incluir al alumno de Arte pero no al de Carpintería
        self.assertIn(self.alumno_arte, alumnos_list)
        self.assertNotIn(self.alumno_carp, alumnos_list)

    def test_exportar_excel_format(self):
        self.client.login(username="admin", password="adminpassword")
        response = self.client.get(reverse("cobros:dashboard") + "?export=excel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn("planilla_cobros_", response['Content-Disposition'])
        
        # Comprobar que comience con la marca BOM UTF-8 y contenga los delimitadores correspondientes
        content_decoded = response.content.decode('utf-8')
        self.assertIn("Alumno;DNI;Subprograma;Espacio;Sala;Importe;Estado;Fecha de Pago;Método;Deuda Histórica", content_decoded)
        # Resumen al final de los registros
        self.assertIn("Resumen de Planilla", content_decoded)
        self.assertIn("Total Alumnos", content_decoded)

    def test_exportar_pdf_format(self):
        self.client.login(username="admin", password="adminpassword")
        response = self.client.get(reverse("cobros:dashboard") + "?export=pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn("planilla_cobros_", response['Content-Disposition'])
        # Formato de cabecera PDF
        self.assertTrue(response.content.startswith(b'%PDF'))


