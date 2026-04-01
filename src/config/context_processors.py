from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.core.club import get_club_settings


def ga_tracking_id(request):
    """Fuegt Google Analytics Tracking ID zum Template Context hinzu"""
    return {
        "ga_tracking_id": getattr(settings, "GA_TRACKING_ID", ""),
    }


def club_info(request):
    user = getattr(request, "user", None)
    profile = None
    if getattr(user, "is_authenticated", False):
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None
    pending_member_limited_access = bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "role", "") == "member"
        and profile is not None
        and profile.status == "pending"
        and profile.onboarding_complete
    )
    return {
        **get_club_settings(),
        "pending_member_limited_access": pending_member_limited_access,
    }
