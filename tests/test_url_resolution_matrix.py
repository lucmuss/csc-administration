from __future__ import annotations

import uuid

import pytest
from django.urls import get_resolver, resolve, reverse
from django.urls.resolvers import URLPattern, URLResolver


def _dummy_for_converter(conv_name: str):
    mapping = {
        "int": 1,
        "slug": "demo-slug",
        "str": "demo",
        "uuid": uuid.UUID("12345678-1234-5678-1234-567812345678"),
        "path": "demo/path",
    }
    return mapping.get(conv_name, "demo")


def _collect_named_patterns(urlpatterns, namespace_prefix=""):
    entries = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            ns = namespace_prefix
            if pattern.namespace:
                ns = f"{namespace_prefix}:{pattern.namespace}" if namespace_prefix else pattern.namespace
            entries.extend(_collect_named_patterns(pattern.url_patterns, ns))
        elif isinstance(pattern, URLPattern) and pattern.name:
            full_name = f"{namespace_prefix}:{pattern.name}" if namespace_prefix else pattern.name
            converters = getattr(pattern.pattern, "converters", {})
            kwargs = {name: _dummy_for_converter(conv.__class__.__name__.replace("Converter", "").lower()) for name, conv in converters.items()}
            if full_name == "admin:app_list" and "app_label" not in kwargs:
                kwargs["app_label"] = "auth"
            entries.append((full_name, kwargs))
    return entries


@pytest.mark.django_db
def test_all_named_urls_reverse_and_resolve():
    resolver = get_resolver()
    named = _collect_named_patterns(resolver.url_patterns)
    assert named, "Keine benannten URLs gefunden"

    failures = []
    for name, kwargs in named:
        try:
            url = reverse(name, kwargs=kwargs or None)
            match = resolve(url)
            assert match.view_name == name
        except Exception as exc:
            failures.append((name, kwargs, str(exc)))

    assert not failures, f"URL-Reverse/Resolve Fehler: {failures[:10]}"


@pytest.mark.django_db
def test_non_existing_url_returns_404(client):
    response = client.get("/this/path/does/not/exist/")
    assert response.status_code == 404
