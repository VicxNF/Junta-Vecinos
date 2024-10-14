from django.apps import AppConfig


class JuntaVecinosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'junta_vecinos'

    def ready(self):
        import junta_vecinos.signals
