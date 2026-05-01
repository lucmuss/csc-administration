import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_privacy_page_renders_grouped_sections(client):
    response = client.get(reverse("core:privacy"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Verantwortlicher" in html
    assert "Kontakt und Fachbereiche" in html
    assert "Datenschutzkontakt" in html
    assert "Praevention" in html
