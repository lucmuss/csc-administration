import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_manifest_and_service_worker_are_available(client):
    manifest_response = client.get(reverse('manifest'))
    assert manifest_response.status_code == 200
    assert 'application/manifest+json' in manifest_response['Content-Type']

    manifest = json.loads(manifest_response.content.decode('utf-8'))
    assert manifest['name'] == 'CSC Verwaltung'
    icon_sizes = {icon['sizes'] for icon in manifest['icons']}
    assert {'192x192', '512x512'} <= icon_sizes

    worker_response = client.get(reverse('offline_js'))
    assert worker_response.status_code == 200
    assert 'application/javascript' in worker_response['Content-Type']
    worker_source = worker_response.content.decode('utf-8')
    assert "const CACHE_NAME = 'csc-pwa-v2'" in worker_source
    assert "const BYPASS_PREFIXES = ['/accounts/', '/members/register/']" in worker_source
    assert "caches.match('/offline/')" in worker_source


@pytest.mark.django_db
def test_base_template_contains_pwa_and_mobile_navigation(client):
    response = client.get(reverse('accounts:login'))
    assert response.status_code == 200
    html = response.content.decode('utf-8')

    assert 'rel="manifest"' in html
    assert 'id="mobile-menu-button"' in html
    assert 'aria-controls="main-nav"' in html
    assert "navigator.serviceWorker.register('/offline.js?v=2')" in html


def test_touch_target_styles_are_present():
    with open('static/src/input.css', encoding='utf-8') as css_file:
        css = css_file.read()

    assert '.touch-target' in css
    assert 'min-height: 44px;' in css
    assert 'min-width: 44px;' in css
    assert '.btn-mobile-nav' in css
