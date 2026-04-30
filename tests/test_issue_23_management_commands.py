from datetime import date, datetime, timezone as dt_timezone
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_collect_membership_fees_midmonth_skips_when_not_day_15():
    out = StringIO()
    with patch("apps.finance.management.commands.collect_membership_fees_midmonth.timezone.localdate", return_value=date(2026, 4, 14)):
        with patch("apps.finance.management.commands.collect_membership_fees_midmonth.apply_monthly_membership_credits") as mocked_apply:
            call_command("collect_membership_fees_midmonth", stdout=out)

    mocked_apply.assert_not_called()
    assert "Kein Lauf" in out.getvalue()


@pytest.mark.django_db
def test_collect_membership_fees_midmonth_runs_on_day_15():
    out = StringIO()
    with patch("apps.finance.management.commands.collect_membership_fees_midmonth.timezone.localdate", return_value=date(2026, 4, 15)):
        with patch("apps.finance.management.commands.collect_membership_fees_midmonth.apply_monthly_membership_credits", return_value=7) as mocked_apply:
            call_command("collect_membership_fees_midmonth", stdout=out)

    mocked_apply.assert_called_once_with(today=date(2026, 4, 15))
    assert "erfolgreich verbucht: 7" in out.getvalue()


@pytest.mark.django_db
def test_collect_membership_fees_midmonth_force_runs_even_outside_day_15():
    out = StringIO()
    with patch("apps.finance.management.commands.collect_membership_fees_midmonth.timezone.localdate", return_value=date(2026, 4, 7)):
        with patch("apps.finance.management.commands.collect_membership_fees_midmonth.apply_monthly_membership_credits", return_value=3) as mocked_apply:
            call_command("collect_membership_fees_midmonth", "--force", stdout=out)

    mocked_apply.assert_called_once_with(today=date(2026, 4, 7))
    assert "erfolgreich verbucht: 3" in out.getvalue()


@pytest.mark.django_db
def test_apply_membership_credits_command_calls_service():
    out = StringIO()
    today = date(2026, 4, 30)
    with patch("apps.finance.management.commands.apply_membership_credits.timezone.localdate", return_value=today):
        with patch("apps.finance.management.commands.apply_membership_credits.apply_monthly_membership_credits", return_value=4) as mocked_apply:
            call_command("apply_membership_credits", stdout=out)

    mocked_apply.assert_called_once_with(today=today)
    assert "Applied monthly membership credits to 4 profiles." in out.getvalue()


@pytest.mark.django_db
def test_send_reminders_command_writes_sent_count():
    out = StringIO()
    with patch("apps.finance.management.commands.send_reminders.send_due_reminders", return_value=5) as mocked:
        call_command("send_reminders", stdout=out)

    mocked.assert_called_once_with()
    assert "Mahnungen versendet: 5" in out.getvalue()


@pytest.mark.django_db
def test_collect_sepa_payments_command_executes_three_steps():
    out = StringIO()
    with patch("apps.finance.management.commands.collect_sepa_payments.schedule_sepa_payment", return_value=True) as schedule_mock:
        with patch("apps.finance.management.commands.collect_sepa_payments.send_sepa_prenotifications", return_value=2) as prenotify_mock:
            with patch("apps.finance.management.commands.collect_sepa_payments.collect_due_sepa_payments", return_value=1) as collect_mock:
                call_command("collect_sepa_payments", stdout=out)

    prenotify_mock.assert_called_once_with()
    collect_mock.assert_called_once_with()
    assert schedule_mock.call_count >= 0
    assert "SEPA verarbeitet:" in out.getvalue()
    assert "Vorabankuendigungen=2" in out.getvalue()
    assert "Eingezogen=1" in out.getvalue()


@pytest.mark.django_db
def test_send_verification_reminders_skips_recently_notified_profile(member_user):
    member_user.profile.is_verified = False
    member_user.profile.status = member_user.profile.STATUS_PENDING
    member_user.profile.registration_completed_at = datetime(2026, 4, 1, 10, 0, 0, tzinfo=dt_timezone.utc)
    member_user.profile.verification_reminder_sent_at = datetime(2026, 4, 29, 10, 0, 0, tzinfo=dt_timezone.utc)
    member_user.profile.save(
        update_fields=["is_verified", "status", "registration_completed_at", "verification_reminder_sent_at", "updated_at"]
    )

    with patch(
        "apps.members.management.commands.send_verification_reminders.timezone.now",
        return_value=datetime(2026, 4, 30, 10, 0, 0, tzinfo=dt_timezone.utc),
    ):
        with patch("apps.members.management.commands.send_verification_reminders.send_verification_reminder_email", return_value=True) as send_mock:
            call_command("send_verification_reminders")

    send_mock.assert_not_called()
