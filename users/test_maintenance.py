from django.test import TestCase, override_settings
from django.urls import reverse

class MaintenanceModeTests(TestCase):
    def setUp(self):
        # Aseguramos que el host sea permitido para los tests
        self.client.defaults['SERVER_NAME'] = 'localhost'

    @override_settings(MAINTENANCE_MODE=True, SECURE_SSL_REDIRECT=False)
    def test_root_renders_maintenance_when_active(self):
        """Verifica que la raíz '/' muestre el template de mantenimiento con status 200."""
        response = self.client.get('/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mantenimiento.html')
        content = response.content.decode('utf-8')
        self.assertIn('10:00 hs a 12:00 hs', content)
        self.assertIn('Sistema Temporalmente Fuera de Servicio', content)
        self.assertIn('bases de datos', content)
        self.assertIn('Sistema Presente GRCU', content)

    @override_settings(MAINTENANCE_MODE=True, SECURE_SSL_REDIRECT=False)
    def test_authenticated_endpoints_intercepted_with_503(self):
        """Verifica que cualquier ruta del sistema retorne 503 con la pantalla de mantenimiento."""
        response = self.client.get('/accounts/login/', secure=True)
        self.assertEqual(response.status_code, 503)
        self.assertTemplateUsed(response, 'mantenimiento.html')
        self.assertEqual(response.headers.get('Retry-After'), '7200')

    @override_settings(MAINTENANCE_MODE=True, SECURE_SSL_REDIRECT=False)
    def test_health_check_bypasses_maintenance(self):
        """Verifica que el endpoint /health/ para Docker/Dokploy funcione sin ser bloqueado."""
        response = self.client.get('/health/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), 'OK')

    @override_settings(MAINTENANCE_MODE=True, SECURE_SSL_REDIRECT=False)
    def test_mantenimiento_direct_url(self):
        """Verifica que la ruta /mantenimiento/ responda correctamente con 200."""
        response = self.client.get('/mantenimiento/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mantenimiento.html')

    @override_settings(MAINTENANCE_MODE=True, SECURE_SSL_REDIRECT=False)
    def test_admin_secret_bypass(self):
        """Verifica que el parámetro de bypass permita acceso en caso de necesidad administrativa."""
        response = self.client.get('/accounts/login/?bypass_mantenimiento=grcu_admin_2026', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    @override_settings(MAINTENANCE_MODE=False, SECURE_SSL_REDIRECT=False)
    def test_normal_operation_when_maintenance_disabled(self):
        """Verifica que cuando el mantenimiento está desactivado, el sistema opere normalmente."""
        response = self.client.get('/', secure=True)
        # Redirige al login para usuarios anónimos
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_clean_env_bool_variants(self):
        """Valida que todas las variantes de strings provenientes de Dokploy/env se parseen correctamente."""
        from config.settings import clean_env_bool
        # Casos verdaderos
        self.assertTrue(clean_env_bool('True'))
        self.assertTrue(clean_env_bool('true'))
        self.assertTrue(clean_env_bool('TRUE'))
        self.assertTrue(clean_env_bool('1'))
        self.assertTrue(clean_env_bool('"true"'))
        self.assertTrue(clean_env_bool("'true'"))
        self.assertTrue(clean_env_bool('  true  '))
        self.assertTrue(clean_env_bool('"1"'))
        self.assertTrue(clean_env_bool('yes'))
        self.assertTrue(clean_env_bool('on'))
        self.assertTrue(clean_env_bool('activo'))
        self.assertTrue(clean_env_bool('habilitado'))

        # Casos falsos
        self.assertFalse(clean_env_bool('False'))
        self.assertFalse(clean_env_bool('false'))
        self.assertFalse(clean_env_bool('FALSE'))
        self.assertFalse(clean_env_bool('0'))
        self.assertFalse(clean_env_bool('"false"'))
        self.assertFalse(clean_env_bool("'false'"))
        self.assertFalse(clean_env_bool('  false  '))
        self.assertFalse(clean_env_bool('"0"'))
        self.assertFalse(clean_env_bool('no'))
        self.assertFalse(clean_env_bool('off'))
        self.assertFalse(clean_env_bool('inactivo'))
        self.assertFalse(clean_env_bool('deshabilitado'))
        self.assertFalse(clean_env_bool(''))
        self.assertFalse(clean_env_bool(None))
