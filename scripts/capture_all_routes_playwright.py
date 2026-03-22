#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.urls import URLPattern, URLResolver, get_resolver


BASE_URL = os.getenv("CSC_CAPTURE_BASE_URL", "http://127.0.0.1:18086").rstrip("/")
LOGIN_URL = f"{BASE_URL}/accounts/login/"
ADMIN_EMAIL = os.getenv("CSC_CAPTURE_ADMIN_EMAIL", "capture-admin@csc.local")
ADMIN_PASSWORD = os.getenv("CSC_CAPTURE_ADMIN_PASSWORD", "StrongPass123!")
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJECT_ROOT / "output" / "gui-screenshots" / f"all-routes-{TIMESTAMP}"
MANIFEST_PATH = OUT_ROOT / "manifest.json"

DESKTOP = (1440, 900)
MOBILE = (390, 844)

BLOCKED_EXACT = {
    "/accounts/dev-login/",
    "/accounts/logout/",
    "/admin/logout/",
    "/admin/jsi18n/",
    "/members/export/",
    "/orders/cart/add/",
    "/orders/cart/clear/",
    "/manifest.json",
    "/offline.js",
}
BLOCKED_PARTS = ("/send/", "/assign-inventory/", "/update-status/")


def walk(patterns, prefix: str = "") -> list[str]:
    routes: list[str] = []
    for pattern in patterns:
        raw = str(pattern.pattern)
        combined = f"{prefix}{raw}"
        if isinstance(pattern, URLPattern):
            routes.append(combined)
        elif isinstance(pattern, URLResolver):
            routes.extend(walk(pattern.url_patterns, combined))
    return routes


def normalize_route(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return "/"
    return "/" + value.lstrip("/")


def is_safe_page_route(route: str) -> bool:
    if route in BLOCKED_EXACT:
        return False
    if any(token in route for token in ("<", "(?P<", "^", "$")):
        return False
    if route.endswith((".js", ".json", ".gif")):
        return False
    if "/api/" in route:
        return False
    if route.startswith("/admin/r/"):
        return False
    if any(part in route for part in BLOCKED_PARTS):
        return False
    return True


def slugify(route: str) -> str:
    if route == "/":
        return "home"
    slug = route.strip("/").replace("/", "--")
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-").lower()
    return slug or "route"


def discover_routes() -> list[str]:
    django.setup()
    raw_routes = walk(get_resolver().url_patterns)
    routes = sorted({normalize_route(route) for route in raw_routes} | {"/"})
    return [route for route in routes if is_safe_page_route(route)]


def new_context(browser: Browser, viewport_name: str) -> BrowserContext:
    if viewport_name == "mobile":
        return browser.new_context(
            viewport={"width": MOBILE[0], "height": MOBILE[1]},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )
    return browser.new_context(viewport={"width": DESKTOP[0], "height": DESKTOP[1]})


def login(context: BrowserContext) -> None:
    page = context.new_page()
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
    page.fill("#id_username", ADMIN_EMAIL)
    page.fill("#id_password", ADMIN_PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(900)
    if urlparse(page.url).path.startswith("/accounts/login/"):
        body = page.locator("body").inner_text(timeout=2000)
        raise RuntimeError(f"Login failed; still on login page. Body excerpt: {body[:200]!r}")
    page.close()


def classify_public_routes(browser: Browser, routes: list[str]) -> tuple[list[str], list[str]]:
    context = new_context(browser, "desktop")
    page = context.new_page()
    public: list[str] = []
    protected: list[str] = []
    for route in routes:
        try:
            page.goto(f"{BASE_URL}{route}", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(250)
            final_path = urlparse(page.url).path or "/"
            if route != "/accounts/login/" and (
                final_path.startswith("/accounts/login/")
                or final_path.startswith("/admin/login/")
            ):
                protected.append(route)
            else:
                public.append(route)
        except Exception:
            protected.append(route)
    context.close()
    return public, protected


def capture_routes(
    browser: Browser,
    routes: list[str],
    viewport_name: str,
    state_name: str,
    do_login: bool,
) -> list[dict[str, str | int | None]]:
    context = new_context(browser, viewport_name)
    if do_login:
        login(context)

    target_dir = OUT_ROOT / viewport_name / state_name
    target_dir.mkdir(parents=True, exist_ok=True)
    page = context.new_page()
    total = len(routes)
    records: list[dict[str, str | int | None]] = []

    for idx, route in enumerate(routes, start=1):
        url = f"{BASE_URL}{route}"
        file_path = target_dir / f"{idx:03d}-{slugify(route)}.png"
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(500)
            final_url = page.url
            status = response.status if response else None
            page.screenshot(path=str(file_path), full_page=True)
            print(
                f"[{viewport_name}/{state_name}] {idx}/{total} {route} -> "
                f"{urlparse(final_url).path or '/'} status={status}"
            )
            records.append(
                {
                    "route": route,
                    "requested_url": url,
                    "final_url": final_url,
                    "status": status,
                    "screenshot": str(file_path.relative_to(PROJECT_ROOT)),
                    "error": None,
                }
            )
        except Exception as exc:
            print(f"[{viewport_name}/{state_name}] {idx}/{total} {route} ERROR {exc}")
            records.append(
                {
                    "route": route,
                    "requested_url": url,
                    "final_url": page.url,
                    "status": None,
                    "screenshot": None,
                    "error": str(exc),
                }
            )

    context.close()
    return records


def main() -> int:
    routes = discover_routes()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {OUT_ROOT}")
    print(f"Total safe routes: {len(routes)}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        public_routes, protected_routes = classify_public_routes(browser, routes)

        print(f"Public routes: {len(public_routes)}")
        print(f"Protected routes: {len(protected_routes)}")

        manifest = {
            "generated_at": TIMESTAMP,
            "base_url": BASE_URL,
            "login_url": LOGIN_URL,
            "public_route_count": len(public_routes),
            "protected_route_count": len(protected_routes),
            "all_safe_routes": routes,
            "public_routes": public_routes,
            "protected_routes": protected_routes,
            "captures": {},
        }

        capture_plan = [
            ("desktop", "guest-public", public_routes, False),
            ("mobile", "guest-public", public_routes, False),
            ("desktop", "admin-all", routes, True),
            ("mobile", "admin-all", routes, True),
        ]
        for viewport_name, state_name, capture_list, do_login in capture_plan:
            manifest["captures"][f"{viewport_name}:{state_name}"] = capture_routes(
                browser,
                capture_list,
                viewport_name,
                state_name,
                do_login=do_login,
            )

        browser.close()

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Manifest written to: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
