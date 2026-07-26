from django.apps import AppConfig


class PyADCSConnectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PyADCSConnector'
    label = 'PyADCSConnector'

    def ready(self):
        import PyADCSConnector.signals
