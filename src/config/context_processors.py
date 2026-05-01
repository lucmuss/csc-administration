from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import OperationalError, ProgrammingError
from functools import lru_cache
import subprocess

from apps.core.club import (
    ACTIVE_FEDERAL_STATE_COOKIE,
    ACTIVE_FEDERAL_STATE_SESSION_KEY,
    ACTIVE_SOCIAL_CLUB_COOKIE,
    ACTIVE_SOCIAL_CLUB_SESSION_KEY,
    get_club_settings,
    resolve_active_federal_state,
    resolve_active_social_club,
)
from apps.core.models import SocialClub


def ga_tracking_id(request):
    """Fuegt Google Analytics Tracking ID zum Template Context hinzu"""
    return {
        "ga_tracking_id": getattr(settings, "GA_TRACKING_ID", ""),
    }


@lru_cache(maxsize=1)
def _resolve_app_version() -> str:
    configured = (getattr(settings, "APP_VERSION", "") or "").strip()
    if configured:
        parts = configured.split(".")
        if len(parts) == 3 and parts[2] == "0" and all(part.isdigit() for part in parts):
            return ".".join(parts[:2])
        return configured
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if tag:
            return tag
    except Exception:
        pass
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if commit:
            return f"dev-{commit}"
    except Exception:
        pass
    return "dev"


def app_version(request):
    return {"app_version": _resolve_app_version()}


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
        and not profile.is_verified
        and profile.onboarding_complete
    )
    active_social_club = resolve_active_social_club(request)
    active_federal_state = resolve_active_federal_state(request)
    active_federal_state_label = dict(SocialClub.FEDERAL_STATE_CHOICES).get(active_federal_state, "")
    try:
        if (
            getattr(user, "is_authenticated", False)
            and not getattr(user, "is_superuser", False)
            and getattr(user, "social_club_id", None)
        ):
            social_club_options = list(
                SocialClub.objects.filter(
                id=user.social_club_id,
                is_active=True,
                is_approved=True,
            )
            )
        else:
            social_club_options = list(
                SocialClub.objects.filter(is_active=True, is_approved=True).order_by("name")[:200]
            )
    except (RuntimeError, OperationalError, ProgrammingError):
        social_club_options = []
    has_saved_club = bool(request.session.get(ACTIVE_SOCIAL_CLUB_SESSION_KEY) or request.COOKIES.get(ACTIVE_SOCIAL_CLUB_COOKIE))
    has_saved_state = bool(request.session.get(ACTIVE_FEDERAL_STATE_SESSION_KEY) or request.COOKIES.get(ACTIVE_FEDERAL_STATE_COOKIE))
    show_social_club_switcher = bool(
        social_club_options
        and (
            getattr(user, "is_superuser", False)
            or not (has_saved_club and has_saved_state)
        )
    )
    return {
        **get_club_settings(social_club=active_social_club),
        "pending_member_limited_access": pending_member_limited_access,
        "active_social_club": active_social_club,
        "active_federal_state": active_federal_state,
        "active_federal_state_label": active_federal_state_label,
        "federal_state_options": SocialClub.FEDERAL_STATE_CHOICES,
        "social_club_switch_options": social_club_options,
        "show_social_club_switcher": show_social_club_switcher,
    }
