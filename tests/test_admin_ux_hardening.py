from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.finance.models import SepaMandate
from apps.governance.forms import IntegrationEndpointForm
from apps.messaging.forms import EmailGroupForm
from apps.members.models import Profile


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        email="admin-ux@example.com",
        password="StrongPass123!",
        first_name="Ada",
        last_name="Admin",
        role=User.ROLE_BOARD,
        is_staff=True,
        is_superuser=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1986, 1, 1),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100099,
        monthly_counter_key="2026-03",
        desired_join_date=date(2026, 4, 1),
        street_address="Teststrasse 1",
        postal_code="04107",
        city="Leipzig",
        phone="+49123456789",
        bank_name="GLS Bank",
        account_holder_name="Ada Admin",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE44500105175407324931",
        bic="INGDDEFFXXX",
        account_holder="Ada Admin",
        mandate_reference="MANDATE-ADA-1",
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


@pytest.fixture
def staff_user(db):
    user = User.objects.create_user(
        email="staff-ux@example.com",
        password="StrongPass123!",
        first_name="Steffi",
        last_name="Staff",
        role=User.ROLE_STAFF,
        is_staff=True,
    )
    profile = Profile.objects.create(
        user=user,
        birth_date=date(1989, 2, 2),
        status=Profile.STATUS_ACTIVE,
        is_verified=True,
        member_number=100120,
        monthly_counter_key="2026-03",
        desired_join_date=date(2026, 4, 1),
        street_address="Nebenstrasse 2",
        postal_code="04107",
        city="Leipzig",
        phone="+49176543210",
        bank_name="GLS Bank",
        account_holder_name="Steffi Staff",
        privacy_accepted=True,
        direct_debit_accepted=True,
        no_other_csc_membership=True,
        german_residence_confirmed=True,
        minimum_age_confirmed=True,
        id_document_confirmed=True,
        important_newsletter_opt_in=True,
        registration_completed_at=timezone.now(),
    )
    mandate = SepaMandate.objects.create(
        profile=profile,
        iban="DE12500105170648489890",
        bic="GENODEM1GLS",
        account_holder="Steffi Staff",
        mandate_reference="MANDATE-STAFF-1",
    )
    profile.sepa_mandate = mandate
    profile.save(update_fields=["sepa_mandate", "updated_at"])
    return user


def test_email_group_form_rejects_empty_and_html_name():
    empty_form = EmailGroupForm(data={"name": " ", "description": "", "is_active": True})
    html_form = EmailGroupForm(data={"name": "<b>Vorstand</b>", "description": "", "is_active": True})

    assert not empty_form.is_valid()
    assert not html_form.is_valid()
    assert "name" in empty_form.errors
    assert "name" in html_form.errors


@pytest.mark.django_db
def test_governance_meetings_uses_datetime_local_input(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("governance:meetings"))

    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert 'type="date"' in html
    assert 'type="time"' in html
    assert "Kalender oeffnen" in html
    assert "Uhrzeit oeffnen" in html


@pytest.mark.django_db
def test_grow_cycle_form_marks_required_fields_and_uses_date_inputs(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("cultivation:grow_cycle_create"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Pflichtfelder sind markiert" in html
    assert "Name *" in html
    assert 'type="date"' in html


def test_integration_endpoint_form_rejects_invalid_urls():
    invalid_form = IntegrationEndpointForm(
        data={
            "name": "Buchhaltung",
            "integration_type": "external",
            "endpoint_url": "buchhaltung-intern",
            "auth_header_name": "Authorization",
            "auth_token": "",
            "enabled": True,
            "subscribed_events_input": "governance.task.updated",
            "resource_scope_input": "members",
        }
    )
    valid_form = IntegrationEndpointForm(
        data={
            "name": "Buchhaltung",
            "integration_type": "external",
            "endpoint_url": "https://buchhaltung.example/api/webhook",
            "auth_header_name": "Authorization",
            "auth_token": "",
            "enabled": True,
            "subscribed_events_input": "governance.task.updated",
            "resource_scope_input": "members",
        }
    )

    assert not invalid_form.is_valid()
    assert "endpoint_url" in invalid_form.errors
    assert valid_form.is_valid()


@pytest.mark.django_db
def test_admin_lists_have_filter_reset_buttons(client, admin_user):
    client.force_login(admin_user)

    members_response = client.get(reverse("members:directory"))
    orders_response = client.get(reverse("orders:admin_list"))

    assert members_response.status_code == 200
    assert "Filter zuruecksetzen" in members_response.content.decode("utf-8")
    assert orders_response.status_code == 200
    assert "Filter zuruecksetzen" in orders_response.content.decode("utf-8")


@pytest.mark.django_db
def test_flash_labels_are_localized_and_compliance_report_is_tabular(client, admin_user):
    client.force_login(admin_user)

    annual_response = client.get(reverse("compliance:annual_report"), {"year": "ungueltig"})
    html = annual_response.content.decode("utf-8")

    assert annual_response.status_code == 200
    assert "Zurueck zu Compliance" in html
    assert "<table" in html
    assert "Monat" in html
    assert "Hinweis" in html


@pytest.mark.django_db
def test_compliance_dashboard_shows_help_text(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("compliance:dashboard"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Verdachtsfaelle und Meldungen" in html
    assert "Wann entsteht ein Verdachtsfall?" in html


@pytest.mark.django_db
def test_governance_dashboard_contains_anchor_navigation(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("governance:dashboard"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'href="#governance-meetings"' in html
    assert 'href="#governance-integrations"' in html
    assert 'href="#governance-tasks"' in html


@pytest.mark.django_db
def test_governance_tasks_support_drag_drop_markup(client, admin_user):
    from apps.governance.models import BoardTask

    BoardTask.objects.create(title="Task Drag", status=BoardTask.STATUS_TODO, priority=BoardTask.PRIORITY_MEDIUM, created_by=admin_user)
    client.force_login(admin_user)

    response = client.get(reverse("governance:tasks"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'data-task-dropzone="true"' in html
    assert 'data-task-card="true"' in html
    assert "dragstart" in html


@pytest.mark.django_db
def test_integrations_page_shows_help_for_tokens_and_reachability(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("governance:integrations"))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Test-Hook" in html
    assert "Token & Header" in html
    assert "Erreichbarkeit" in html


@pytest.mark.django_db
def test_staff_member_detail_hides_bank_panel_for_foreign_profile(client, staff_user, member_user):
    client.force_login(staff_user)

    response = client.get(reverse("members:detail", args=[member_user.profile.id]))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Bankverbindung und Lastschrift" not in html
    assert "••••" not in html
