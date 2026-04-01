#!/usr/bin/env python3
"""
Screenshot generator for CSC Administration.
Follows agent-policies/10-general/17.new.screenshots.rule.md:
  - output/feedback/routes/<slug>/<viewport>/screenshot.png
  - output/feedback/routes/<slug>/<viewport>/transcript.md
  - output/feedback/routes/<slug>/<viewport>/meta.json
Viewports: desktop 1440x900, mobile 390x844
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser

BASE_URL = "http://localhost:8000"
OUTPUT_ROOT = Path(__file__).parent.parent / "output" / "feedback" / "routes"
CREDENTIALS = {"email": "board@test.local", "password": "testpass123"}

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

# Routes to capture: (path, label_for_transcript)
ROUTES = [
    ("/accounts/login/", "Login-Seite"),
    ("/accounts/register/", "Registrierung"),
    ("/", "Dashboard"),
    ("/members/admin/", "Mitglieder-Cockpit"),
    ("/finance/", "Finanz-Dashboard"),
    ("/finance/invoices/", "Rechnungsliste"),
    ("/finance/payments/", "Zahlungsliste"),
    ("/compliance/", "Compliance-Dashboard"),
    ("/cultivation/", "Anbau-Dashboard"),
    ("/cultivation/cycles/", "Anbauzyklen"),
    ("/cultivation/plants/", "Pflanzen"),
    ("/cultivation/harvest/", "Ernteliste"),
    ("/inventory/strains/", "Sortenübersicht"),
    ("/inventory/locations/", "Lagerorte"),
    ("/orders/shop/", "Shop"),
    ("/participation/", "Partizipation"),
    ("/messaging/", "Messaging-Dashboard"),
    ("/governance/", "Governance-Dashboard"),
    ("/governance/meetings/", "Sitzungen"),
    ("/governance/tasks/", "Aufgaben"),
    ("/governance/records/", "Beschlüsse"),
]


def slugify(path: str) -> str:
    """Convert URL path to folder slug per rule 17."""
    s = path.lower().strip("/")
    # Normalize dynamic segments
    s = re.sub(r"/\d+(/|$)", r"/[id]\1", s)
    s = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(/|$)", r"/[id]\1", s)
    # Replace slashes and non-alnum
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "root"


def git_info() -> dict:
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        return {"branch": branch, "commit": commit}
    except Exception:
        return {}


def write_meta(folder: Path, route: str, viewport_name: str, size: dict) -> None:
    slug = slugify(route)
    meta = {
        "route": route,
        "slug": slug,
        "url": BASE_URL + route,
        "viewport": viewport_name,
        "viewport_size": {"w": size["width"], "h": size["height"]},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": git_info(),
        "playwright": {"browser": "chromium"},
    }
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def write_transcript(folder: Path, route: str, viewport_name: str, label: str) -> None:
    transcript_path = folder / "transcript.md"
    if not transcript_path.exists():
        transcript_path.write_text(
            f"# Transcript (Voice → Text)\n\nRoute: {route}\nViewport: {viewport_name}\n\n"
            f"## Notes\n- {label}\n\n## Numbered refs (optional)\n1:\n2:\n3:\n"
        )


def login(page: Page) -> None:
    page.goto(BASE_URL + "/accounts/login/")
    page.fill("input[name='username'], input[name='email'], input[type='email']", CREDENTIALS["email"])
    page.fill("input[name='password'], input[type='password']", CREDENTIALS["password"])
    page.click("button[type='submit'], input[type='submit']")
    page.wait_for_load_state("networkidle")


def capture_route(page: Page, route: str, label: str, viewport_name: str, size: dict) -> None:
    slug = slugify(route)
    folder = OUTPUT_ROOT / slug / viewport_name
    folder.mkdir(parents=True, exist_ok=True)

    url = BASE_URL + route
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)

    # Full-page screenshot
    page.screenshot(path=str(folder / "screenshot.png"), full_page=True, timeout=60000)

    write_meta(folder, route, viewport_name, size)
    write_transcript(folder, route, viewport_name, label)

    print(f"  ✓ {viewport_name:8s}  {route}")


def run() -> None:
    git = git_info()
    print(f"CSC Screenshot Generator — branch: {git.get('branch','?')} @ {git.get('commit','?')}")
    print(f"Output: {OUTPUT_ROOT}\n")

    with sync_playwright() as p:
        for viewport_name, size in VIEWPORTS.items():
            print(f"── {viewport_name.upper()} ({size['width']}×{size['height']}) ──")
            browser: Browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport=size,
                device_scale_factor=2 if viewport_name == "mobile" else 1,
            )
            page = context.new_page()

            # First capture login page without auth
            login_slug = slugify("/accounts/login/")
            login_folder = OUTPUT_ROOT / login_slug / viewport_name
            login_folder.mkdir(parents=True, exist_ok=True)
            page.goto(BASE_URL + "/accounts/login/", wait_until="networkidle")
            page.screenshot(path=str(login_folder / "screenshot.png"), full_page=True)
            write_meta(login_folder, "/accounts/login/", viewport_name, size)
            write_transcript(login_folder, "/accounts/login/", viewport_name, "Login-Seite")
            print(f"  ✓ {viewport_name:8s}  /accounts/login/ (unauthenticated)")

            # Login
            try:
                login(page)
            except Exception as e:
                print(f"  ⚠ Login fehlgeschlagen: {e}")

            # Capture all routes (skip login, already done)
            for route, label in ROUTES:
                if route == "/accounts/login/":
                    continue
                try:
                    capture_route(page, route, label, viewport_name, size)
                except Exception as e:
                    print(f"  ✗ {viewport_name:8s}  {route} → {e}")

            browser.close()
            print()

    print("Fertig.")


if __name__ == "__main__":
    run()
