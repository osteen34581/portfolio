import importlib
import os

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def test_allowed_hosts_can_be_configured_from_environment(self):
        import voice_notes.settings as settings_module

        original_hosts = os.environ.get('ALLOWED_HOSTS')
        try:
            os.environ['ALLOWED_HOSTS'] = 'example.com, app.example.com'
            importlib.reload(settings_module)
            self.assertEqual(settings_module.ALLOWED_HOSTS, ['example.com', 'app.example.com'])
        finally:
            if original_hosts is None:
                os.environ.pop('ALLOWED_HOSTS', None)
            else:
                os.environ['ALLOWED_HOSTS'] = original_hosts
            importlib.reload(settings_module)

    def test_trusted_origins_can_be_configured_from_environment(self):
        import voice_notes.settings as settings_module

        original_origins = os.environ.get('CSRF_TRUSTED_ORIGINS')
        try:
            os.environ['CSRF_TRUSTED_ORIGINS'] = 'https://example.com, https://app.example.com'
            importlib.reload(settings_module)
            self.assertEqual(
                settings_module.CSRF_TRUSTED_ORIGINS,
                ['https://example.com', 'https://app.example.com'],
            )
        finally:
            if original_origins is None:
                os.environ.pop('CSRF_TRUSTED_ORIGINS', None)
            else:
                os.environ['CSRF_TRUSTED_ORIGINS'] = original_origins
            importlib.reload(settings_module)
