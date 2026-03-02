from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import WorkHours
from .services import sync_profile_work_hours


@receiver(post_delete, sender=WorkHours)
def update_profile_hours_on_delete(sender, instance, **kwargs):
    sync_profile_work_hours(instance.profile)
