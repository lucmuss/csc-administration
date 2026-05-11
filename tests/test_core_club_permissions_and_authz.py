from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.core.authz import board_required, staff_or_board_required
from config.context_processors import club_info
from apps.core.club import (
    ACTIVE_FEDERAL_STATE_COOKIE,
    ACTIVE_FEDERAL_STATE_SESSION_KEY,
    ACTIVE_SOCIAL_CLUB_COOKIE,
    ACTIVE_SOCIAL_CLUB_SESSION_KEY,
    get_club_settings,
    resolve_active_federal_state,
    resolve_active_social_club,
)
from apps.core.middleware import NoStorePageCacheMiddleware
from apps.core.models import ClubConfiguration, SocialClub
from apps.core.permissions import is_overadmin
from apps.members.models import Profile


pytestmark = pytest.mark.django_db


def _club(name: str, email: str, *, state: str = SocialClub.BUNDESLAND_SN) -> SocialClub:
    return SocialClub.objects.create(
        name=name,
        email=email,
        street_address="Testweg 1",
        postal_code="04109",
        city="Leipzig",
        phone="+49123456789",
        federal_state=state,
        is_active=True,
        is_approved=True,
    )


def _member(email: str, club: SocialClub | None = None, *, role: str = User.ROLE_MEMBER) -> User:
    user = User.objects.create_user(
        email=email,
        password="StrongPass123!",
        first_name="Vor",
        last_name="Nach",
        role=role,
        is_staff=role in {User.ROLE_STAFF, User.ROLE_BOARD},
        social_club=club,
    )
    Profile.objects.create(
        user=user,
        birth_date=date(1990, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        registration_completed_at=timezone.now(),
        monthly_counter_key=timezone.localdate().strftime("%Y-%m"),
    )
    return user


def _attach_session_and_messages(request):
    middleware = SessionMiddleware(lambda req: HttpResponse("ok"))
    middleware.process_request(request)
    request.session.save()
    setattr(request, "_messages", FallbackStorage(request))


def test_resolve_active_social_club_prefers_non_overadmin_user_assignment(rf):
    own = _club("Eigener Club", "own@example.com")
    selected = _club("Ausgewaehlter Club", "selected@example.com")
    user = _member("member-own@example.com", own)

    request = rf.get("/")
    request.user = user
    request.session = {ACTIVE_SOCIAL_CLUB_SESSION_KEY: selected.id}
    request.COOKIES = {ACTIVE_SOCIAL_CLUB_COOKIE: str(selected.id)}

    assert resolve_active_social_club(request) == own


def test_resolve_active_social_club_uses_session_for_anonymous_user(rf):
    club = _club("Session Club", "session@example.com")
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = {ACTIVE_SOCIAL_CLUB_SESSION_KEY: club.id}
    request.COOKIES = {}

    assert resolve_active_social_club(request) == club


def test_resolve_active_social_club_falls_back_to_first_public_for_anonymous(rf):
    first = _club("A Club", "a@example.com")
    _club("B Club", "b@example.com")
    request = rf.get("/")
    request.user = AnonymousUser()
    request.session = {}
    request.COOKIES = {}

    assert resolve_active_social_club(request) == first


def test_resolve_active_social_club_returns_none_for_authenticated_without_selection(rf):
    user = _member("noclub@example.com", club=None)
    request = rf.get("/")
    request.user = user
    request.session = {}
    request.COOKIES = {}

    assert resolve_active_social_club(request) is None


def test_resolve_active_federal_state_uses_session_or_cookie_and_rejects_invalid(rf):
    request = rf.get("/")
    request.session = {ACTIVE_FEDERAL_STATE_SESSION_KEY: SocialClub.BUNDESLAND_SN}
    request.COOKIES = {}
    assert resolve_active_federal_state(request) == SocialClub.BUNDESLAND_SN

    request2 = rf.get("/")
    request2.session = {}
    request2.COOKIES = {ACTIVE_FEDERAL_STATE_COOKIE: SocialClub.BUNDESLAND_BW}
    assert resolve_active_federal_state(request2) == SocialClub.BUNDESLAND_BW

    request3 = rf.get("/")
    request3.session = {ACTIVE_FEDERAL_STATE_SESSION_KEY: "XX"}
    request3.COOKIES = {}
    assert resolve_active_federal_state(request3) == ""


@override_settings(APP_NAME="CSC App aus Settings", CLUB_NAME="Club aus Settings")
def test_get_club_settings_uses_settings_fallback_and_social_club_override():
    settings_only = get_club_settings()
    assert settings_only["app_name"] == "CSC App aus Settings"
    assert settings_only["club_name"] == "Club aus Settings"

    ClubConfiguration.objects.create(club_name="Konfig Club", app_name="Konfig App")
    configured = get_club_settings()
    assert configured["app_name"] == "Konfig App"
    assert configured["club_name"] == "Konfig Club"

    club = _club("Override Club", "override@example.com")
    club_settings = get_club_settings(social_club=club)
    assert club_settings["club_name"] == "Override Club"
    assert club_settings["club_contact_email"] == "override@example.com"


@override_settings(OVERADMIN_EMAILS={"overadmin@example.com"})
def test_is_overadmin_for_superuser_and_configured_email():
    superuser = User.objects.create_superuser(
        email="super@example.com",
        password="StrongPass123!",
        first_name="Sup",
        last_name="Er",
    )
    configured = _member("overadmin@example.com")
    regular = _member("member-regular@example.com")

    assert is_overadmin(superuser) is True
    assert is_overadmin(configured) is True
    assert is_overadmin(regular) is False
    assert is_overadmin(AnonymousUser()) is False


def test_board_required_and_staff_or_board_required_decorators(rf):
    board_user = _member("board-deco@example.com", role=User.ROLE_BOARD)
    staff_user = _member("staff-deco@example.com", role=User.ROLE_STAFF)
    member_user = _member("member-deco@example.com", role=User.ROLE_MEMBER)

    @board_required(lambda user: user.role == User.ROLE_BOARD)
    def board_only_view(request):
        return HttpResponse("board-ok")

    @staff_or_board_required(lambda user: user.role in {User.ROLE_STAFF, User.ROLE_BOARD})
    def staff_or_board_view(request):
        return HttpResponse("staff-board-ok")

    board_request = rf.get("/board-only/")
    _attach_session_and_messages(board_request)
    board_request.user = board_user
    board_response = board_only_view(board_request)
    assert board_response.status_code == 200
    assert board_response.content.decode("utf-8") == "board-ok"

    staff_request = rf.get("/board-only/")
    _attach_session_and_messages(staff_request)
    staff_request.user = staff_user
    staff_denied = board_only_view(staff_request)
    assert staff_denied.status_code == 302
    assert staff_denied.url == reverse("core:dashboard")

    member_request = rf.get("/staff-board/")
    _attach_session_and_messages(member_request)
    member_request.user = member_user
    member_denied = staff_or_board_view(member_request)
    assert member_denied.status_code == 302
    assert member_denied.url == reverse("core:dashboard")

    anon_request = rf.get("/staff-board/")
    _attach_session_and_messages(anon_request)
    anon_request.user = AnonymousUser()
    anon_response = staff_or_board_view(anon_request)
    assert anon_response.status_code == 302
    assert reverse("accounts:login") in anon_response.url


def test_no_store_page_cache_middleware_sets_headers_for_auth_and_auth_paths(rf):
    middleware = NoStorePageCacheMiddleware(lambda request: HttpResponse("ok"))

    authed_request = rf.get("/core/dashboard/")
    authed_request.user = _member("cache-auth@example.com")
    authed_response = middleware(authed_request)
    assert "no-store" in authed_response["Cache-Control"]
    assert authed_response["Pragma"] == "no-cache"
    assert authed_response["Expires"]

    anon_auth_path_request = rf.get("/accounts/login/")
    anon_auth_path_request.user = AnonymousUser()
    anon_auth_path_response = middleware(anon_auth_path_request)
    assert "no-store" in anon_auth_path_response["Cache-Control"]
    assert anon_auth_path_response["Pragma"] == "no-cache"
    assert anon_auth_path_response["Expires"]

    anon_public_request = rf.get("/public/")
    anon_public_request.user = AnonymousUser()
    anon_public_response = middleware(anon_public_request)
    assert "Cache-Control" not in anon_public_response


@override_settings(MAILPIT_UI_ENABLED=True, MAILPIT_HTTP_URL="http://localhost:8025")
def test_club_info_exposes_mailpit_link_for_staff_and_board(rf):
    board_user = _member("board-mailpit@example.com", role=User.ROLE_BOARD)
    request = rf.get("/")
    request.user = board_user
    request.session = {}
    request.COOKIES = {}

    context = club_info(request)

    assert context["show_mailpit_link"] is True
    assert context["mailpit_ui_url"] == "http://localhost:8025"


@override_settings(MAILPIT_UI_ENABLED=True, MAILPIT_HTTP_URL="http://localhost:8025")
def test_club_info_hides_mailpit_link_for_member(rf):
    member_user = _member("member-mailpit@example.com", role=User.ROLE_MEMBER)
    request = rf.get("/")
    request.user = member_user
    request.session = {}
    request.COOKIES = {}

    context = club_info(request)

    assert context["show_mailpit_link"] is False
