from decimal import Decimal

from django.db import models


class Shift(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    required_members = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "id"]

    def __str__(self):
        return f"{self.title} ({self.starts_at:%d.%m.%Y %H:%M})"


class WorkHours(models.Model):
    profile = models.ForeignKey("members.Profile", on_delete=models.CASCADE, related_name="work_hours")
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name="work_hours")
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.profile} - {self.hours}h ({self.date:%d.%m.%Y})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .services import sync_profile_work_hours

        sync_profile_work_hours(self.profile)


class MemberEngagement(models.Model):
    profile = models.OneToOneField("members.Profile", on_delete=models.CASCADE, related_name="engagement")
    required_hours_year = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("20.00"))
    annual_meeting_date = models.DateField(null=True, blank=True)
    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateField(null=True, blank=True)
    registration_completed = models.BooleanField(default=False)
    registration_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    inactivity_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["profile__member_number", "id"]

    def __str__(self):
        return f"Engagement {self.profile}"
