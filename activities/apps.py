from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activities'
    
    def ready(self):
        """Load signals when the app is ready"""
        import activities.signals
