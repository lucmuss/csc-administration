# config/context_processors.py
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist


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
        "club_name": getattr(settings, "CLUB_NAME", ""),
        "club_contact_email": getattr(settings, "CLUB_CONTACT_EMAIL", ""),
        "club_contact_phone": getattr(settings, "CLUB_CONTACT_PHONE", ""),
        "club_contact_address": getattr(settings, "CLUB_CONTACT_ADDRESS", ""),
        "club_membership_email": getattr(settings, "CLUB_MEMBERSHIP_EMAIL", ""),
        "club_prevention_email": getattr(settings, "CLUB_PREVENTION_EMAIL", ""),
        "club_finance_email": getattr(settings, "CLUB_FINANCE_EMAIL", ""),
        "club_language_notice": getattr(settings, "CLUB_LANGUAGE_NOTICE", ""),
        "pending_member_limited_access": pending_member_limited_access,
    }
