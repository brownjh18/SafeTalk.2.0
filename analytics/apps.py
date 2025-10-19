from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        # Import signals to register them
        try:
            from . import signals
        except ImportError:
            pass  # Signals file doesn't exist yet