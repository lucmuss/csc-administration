import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_logout_button_posts_to_logout_view(client, member_user):
    client.force_login(member_user)

    response = client.get(reverse("core:dashboard"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert f'action="{reverse("accounts:logout")}"' in html
    assert 'method="post"' in html


@pytest.mark.django_db
def test_logout_post_redirects_to_login(client, member_user):
    client.force_login(member_user)

    response = client.post(reverse("accounts:logout"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
