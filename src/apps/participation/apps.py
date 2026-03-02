from django.apps import AppConfig


class ParticipationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.participation"
    verbose_name = "Mitwirkung"

    def ready(self):
        from . import signals  # noqa: F401
