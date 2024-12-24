# In courses/apps.py
from django.apps import AppConfig

class CoursesConfig(AppConfig):
    name = 'courses'
    path = '/workspace/courses'

    def ready(self):
        import courses.signals.handlers