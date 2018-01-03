from django.apps import AppConfig


class NjangiConfig(AppConfig):
    name = 'njangi'

    def ready(self):
        import njangi.signals
