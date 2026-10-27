"""Full-page screenshots of the site for design review: py scripts\\screenshots.py

Serves docs/ on a free local port, opens each route at 1280x800 and 375x812 in light and dark colour scheme,
and saves PNGs to runs/screens/ (gitignored). Time-up is reached by shifting Date.now in the page from this script, so the
site needs no debug feature. Prints any page with horizontal scroll or a console error.
"""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "screens"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def start(page):
    page.get_by_role("button", name="Start", exact=True).click()


def started_scrolled(page):
    page.get_by_role("button", name="4 SQL").click()
    page.locator("summary", has_text="Dataset reference").click()
    start(page)
    page.set_viewport_size({"width": page.viewport_size["width"], "height": 560})
    page.wait_for_timeout(1500)
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(300)


def show_answer(page):
    page.locator("summary", has_text="Show answer").click()


def time_up(page):
    start(page)
    page.evaluate("window.__skip = 8 * 60000 + 5000")
    page.wait_for_timeout(600)


def bank_filtered(page):
    page.select_option("#f-subject", "SQL")
    page.fill("#f-text", "invoice")


def tab_focus(page):
    page.keyboard.press("Tab")
    page.get_by_role("button", name="2 Excel").focus()


SHOTS = [
    ("home", "#/", None),
    ("manip-exams", "#/manipulation/exams", None),
    ("exam-E012", "#/manipulation/exams/E012", None),
    ("exam-E012-running", "#/manipulation/exams/E012", started_scrolled),
    ("bank", "#/manipulation/questions", None),
    ("bank-Q045", "#/manipulation/questions/Q045", None),
    ("interp-R004-answer", "#/interpretation/exams/R004", show_answer),
    ("exam-E012-timeup", "#/manipulation/exams/E012", time_up),
    ("bank-filtered", "#/manipulation/questions", bank_filtered),
    ("exam-E012-tab-focus", "#/manipulation/exams/E012", tab_focus),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(QuietHandler, directory=str(ROOT / "docs"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/"
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme in ("light", "dark"):
            for w, h in ((1280, 800), (375, 812)):
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                for name, route, action in SHOTS:
                    page = ctx.new_page()
                    page.add_init_script("window.__skip = 0; const n = Date.now; Date.now = () => n() + window.__skip;")
                    errors = []
                    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                    page.goto(base + route)
                    page.wait_for_selector("main h1")
                    page.evaluate("document.fonts.ready")
                    if action:
                        action(page)
                    if action not in (started_scrolled, tab_focus):
                        page.evaluate("window.scrollTo(0, 0)")
                    if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                        problems.append(f"{name} {w} {scheme}: horizontal scroll")
                    problems += [f"{name} {w} {scheme}: console {e}" for e in errors]
                    if action not in (started_scrolled, tab_focus):
                        page.set_viewport_size({"width": w, "height": page.evaluate("document.documentElement.scrollHeight")})
                    page.screenshot(path=str(OUT / f"{name}-{w}-{scheme}.png"), full_page=action not in (started_scrolled, tab_focus))
                    page.close()
                ctx.close()
        browser.close()
    server.shutdown()
    print("\n".join(problems) or "no horizontal scroll, no console errors")
    print(f"screenshots in {OUT}")


if __name__ == "__main__":
    main()
