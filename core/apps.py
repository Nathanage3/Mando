from django.apps import AppConfig
import os

class CoreConfig(AppConfig):
    name = 'core'
    path = os.path.join(os.path.dirname(__file__), 'courses')

    def ready(self) -> None:
        import core.signals.hanlers