#!/usr/bin/env python3
"""Retry only cultivation/cycles mobile screenshot — no full_page."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from take_screenshots import *

def run():
    vp_name = "mobile"
    size = VIEWPORTS[vp_name]
    route = "/cultivation/cycles/"
    label = "Anbauzyklen"

    print(f"── MOBILE RETRY CYCLES ──")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--font-render-hinting=none"])
        context = browser.new_context(viewport=size, device_scale_factor=1)  # scale_factor=1 to reduce work
        page = context.new_page()

        # Disable font loading to avoid timeout
        page.route("**/*.woff*", lambda r: r.abort())
        page.route("**/*.ttf", lambda r: r.abort())
        page.route("**/*.otf", lambda r: r.abort())

        login(page)

        slug = slugify(route)
        folder = OUTPUT_ROOT / slug / vp_name
        folder.mkdir(parents=True, exist_ok=True)

        page.goto(BASE_URL + route, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # viewport-only screenshot (not full_page) to avoid font-wait
        page.screenshot(path=str(folder / "screenshot.png"), full_page=False, timeout=30000)

        write_meta(folder, route, vp_name, size)
        write_transcript(folder, route, label, vp_name)
        print(f"  ✓ mobile    {route}")
        browser.close()
    print("Fertig.")

if __name__ == "__main__":
    run()
