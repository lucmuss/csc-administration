#!/usr/bin/env python3
"""Retry only failed mobile screenshots."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from take_screenshots import *

FAILED_ROUTES = [
    ("/cultivation/cycles/", "Anbauzyklen"),
    ("/cultivation/plants/", "Pflanzen"),
    ("/cultivation/harvest/", "Ernteliste"),
    ("/messaging/", "Messaging-Dashboard"),
    ("/governance/", "Governance-Dashboard"),
    ("/governance/meetings/", "Sitzungen"),
    ("/governance/tasks/", "Aufgaben"),
    ("/governance/records/", "Beschlüsse"),
]

def run_retry():
    vp_name = "mobile"
    size = VIEWPORTS[vp_name]
    print(f"── MOBILE RETRY ({size['width']}×{size['height']}) ──")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=size, device_scale_factor=2)
        page = context.new_page()
        login(page)
        for route, label in FAILED_ROUTES:
            try:
                capture_route(page, route, label, vp_name, size)
            except Exception as e:
                print(f"  ✗ {route} → {e}")
        browser.close()
    print("Fertig.")

if __name__ == "__main__":
    run_retry()
