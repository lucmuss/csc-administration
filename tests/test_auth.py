import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_success(client, member_user):
    response = client.post(
        reverse("accounts:login"),
        data={"username": member_user.email, "password": "StrongPass123!"},
    )
    assert response.status_code == 302
    assert response.url == reverse("core:dashboard")
