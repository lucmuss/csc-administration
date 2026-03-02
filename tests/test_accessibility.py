from decimal import Decimal

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_navigation_and_messages_use_accessibility_attributes(client):
    response = client.get(reverse('accounts:login'))
    assert response.status_code == 200
    html = response.content.decode('utf-8')

    assert 'aria-label="Hauptnavigation"' in html
    assert 'aria-live="polite"' in html
    assert 'class="skip-link"' in html


@pytest.mark.django_db
def test_shop_form_has_mobile_friendly_labels_and_controls(client, member_user):
    from apps.inventory.models import Strain

    Strain.objects.create(
        name='Lemon Haze',
        thc=Decimal('19.00'),
        cbd=Decimal('0.40'),
        price=Decimal('11.00'),
        stock=Decimal('50.00'),
    )
    client.force_login(member_user)

    response = client.get(reverse('orders:shop'))
    assert response.status_code == 200
    html = response.content.decode('utf-8')

    assert 'class="touch-target field-select"' in html
    assert 'aria-label="Lemon Haze zum Warenkorb hinzufuegen"' in html
    assert 'Menge in Gramm' in html


def test_accessibility_base_styles_are_present():
    with open('static/src/input.css', encoding='utf-8') as css_file:
        css = css_file.read()

    assert 'html {' in css
    assert 'font-size: 16px;' in css
    assert 'focus-visible' in css
    assert '.feedback-success' in css
    assert '.feedback-error' in css
