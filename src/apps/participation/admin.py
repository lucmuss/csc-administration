from django.contrib import admin

from .models import MemberEngagement, Shift, WorkHours


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "ends_at", "required_members")
    search_fields = ("title",)


@admin.register(WorkHours)
class WorkHoursAdmin(admin.ModelAdmin):
    list_display = ("profile", "date", "hours", "approved", "shift")
    list_filter = ("approved", "date")
    search_fields = ("profile__user__email", "profile__member_number")


@admin.register(MemberEngagement)
class MemberEngagementAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "required_hours_year",
        "annual_meeting_date",
        "invitation_sent_at",
        "reminder_sent_at",
        "registration_deadline",
        "registration_completed",
    )
    list_filter = ("registration_completed",)
    search_fields = ("profile__user__email", "profile__member_number")
