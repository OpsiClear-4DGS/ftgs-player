"""Validate the built project-site URLs, real Jensen demo and responsive UI."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import threading
import re

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Existing Chromium executable")
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--network-failures", action="store_true", help="Simulate a blocked large download and interrupted byte ranges")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "dist"
    if not (root / "index.html").exists():
        parser.error("Run npm run build first")
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    prefix = "/ftgs-player/"
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            requests.append(self.path)
            if not self.path.startswith(prefix):
                self.send_error(404)
                return
            self.path = "/" + self.path[len(prefix):]
            super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}{prefix}"

    def fits(page):
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Page overflows"
        for selector in ["#welcome", "#controls"]:
            if not page.locator(selector).is_visible():
                continue
            box = page.locator(selector).bounding_box()
            assert box and box["x"] >= 0 and box["x"] + box["width"] <= page.viewport_size["width"]
            assert box["y"] >= 0 and box["y"] + box["height"] <= page.viewport_size["height"]
        if page.locator("#controls").is_visible():
            box = page.locator("#controls").bounding_box()
            for control in page.locator(".transport > button, .transport > select, #mute-toggle").all():
                if control.is_visible():
                    child = control.bounding_box()
                    assert child["x"] >= box["x"] and child["x"] + child["width"] <= box["x"] + box["width"], "Transport overflows"

    def seek(page, time):
        page.locator("#timeline").evaluate(
            "(el, t) => { el.value = t; el.dispatchEvent(new Event('input')); }", time
        )
        page.wait_for_function("t => window.projectState?.time === t && !window.projectState.playing", arg=time)
        page.wait_for_timeout(1200)  # Finish worker sorting and drawing the requested frame.

    def image(page):
        return Image.open(BytesIO(page.screenshot(clip={"x": 300, "y": 100, "width": 680, "height": 560}))).convert("RGB")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=args.browser, headless=True, args=[
                "--no-sandbox", "--use-angle=swiftshader", "--enable-webgl",
                "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-dev-shm-usage",
            ])
            errors = []
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.on("pageerror", lambda error: errors.append(str(error)))
            def console(message):
                if message.type == "error" and not (args.network_failures and "net::ERR_FAILED" in message.text):
                    errors.append(message.text)
            page.on("console", console)
            blocked = True
            ranges = {}
            if args.network_failures:
                model = (root / "examples/assets/jensen-2m.tsog").read_bytes()
                def scene_request(route):
                    span = route.request.headers.get("range", "")
                    match = re.fullmatch(r"bytes=(\d+)-(\d+)", span)
                    if not match:
                        errors.append("The player tried one large request instead of byte ranges")
                        route.abort("failed")
                        return
                    start, end = map(int, match.groups())
                    assert end - start < 4 * 1024 * 1024
                    ranges[span] = ranges.get(span, 0) + 1
                    if blocked or (start == 4 * 1024 * 1024 and ranges[span] == 1):
                        route.abort("failed")
                        return
                    route.fulfill(status=206, body=model[start:end + 1], headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Range": f"bytes {start}-{end}/{len(model)}",
                    })
                page.route("**/jensen-2m.tsog", scene_request)
            # Observe only the public state events, without exposing website internals.
            page.add_init_script("""(() => {
              const dispatch = EventTarget.prototype.dispatchEvent;
              EventTarget.prototype.dispatchEvent = function(event) {
                if (event.detail && typeof event.detail.pointCount === 'number') {
                  window.projectState = event.detail;
                  if (event.type === 'loaded') window.loadedState = event.detail;
                }
                return dispatch.call(this, event);
              };
            })()""")
            page.goto(url)
            page.evaluate("document.fonts.ready")
            assert page.locator("#empty").is_visible()
            assert not page.locator("#controls").is_visible()
            assert not any(path.endswith(".tsog") for path in requests), "Homepage downloaded a large demo"
            theme = page.evaluate("""() => {
              const css = getComputedStyle(document.documentElement);
              return {void:css.getPropertyValue('--bg-void').trim(), accent:css.getPropertyValue('--accent').trim()};
            }""")
            assert theme == {"void": "#0a0a0a", "accent": "#b8b8b8"}
            fits(page)
            if args.screenshots:
                page.screenshot(path=args.screenshots / "welcome.png")
            page.locator(".example-link").click()
            if args.network_failures:
                page.wait_for_function("document.querySelector('#viewer').dataset.state === 'error'")
                assert "jensen-2m.tsog" in page.locator("#message").inner_text()
                assert page.locator("#retry-example").is_visible()
                assert ranges["bytes=0-4194303"] == 3, "Retries were not bounded"
                blocked = False
                page.locator("#retry-example").click()
            page.wait_for_function("window.loadedState?.pointCount === 2000000", timeout=120000)
            state = page.evaluate("window.loadedState")
            assert state["sourceCount"] == 2000000 and state["nFrames"] == 121
            assert state["fps"] == 24 and state["duration"] == 5
            assert state["audio"]["available"] and not state["audio"]["error"]
            assert not page.locator("#welcome").is_visible()
            assert page.locator("#audio-controls").is_visible()
            assert any(path.endswith("/src/sort-worker.js") for path in requests), "Module worker failed under Pages prefix"
            if args.network_failures:
                assert ranges["bytes=4194304-8388607"] == 2, "Interrupted range was not retried"
                assert not page.locator("#retry-example").is_visible()
            seek(page, .15)
            early = image(page)
            assert sum(ImageStat.Stat(early).stddev) > 15, "Jensen scene is blank"
            seek(page, .7)
            late = image(page)
            assert sum(ImageStat.Stat(ImageChops.difference(early, late)).mean) > 1, "Jensen did not animate"
            seek(page, .3)
            fits(page)
            if args.screenshots:
                page.mouse.move(20, 20)
                page.screenshot(path=args.screenshots / "jensen-2m.png")
            page.locator("#mute-toggle").click()
            assert page.locator("#mute-toggle").get_attribute("aria-pressed") == "true"
            page.locator("#play-toggle").click()
            page.wait_for_function("window.projectState?.playing && window.projectState.time > .32")
            page.locator("#play-toggle").click()
            page.wait_for_function("!window.projectState.playing")
            paused = page.evaluate("window.projectState.time")
            page.wait_for_timeout(300)
            assert page.evaluate("window.projectState.time") == paused
            assert page.locator("#canvas").evaluate("c => c.getContext('webgl2').getError()") == 0
            for width, height in [(390, 844), (320, 568), (844, 390)]:
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(200)
                fits(page)
                if args.screenshots and width == 390:
                    page.screenshot(path=args.screenshots / "jensen-mobile.png")
            assert not errors, errors
            browser.close()
            print("PASS: built Pages paths, opt-in Jensen download, full 2M playback/audio, seeking, pause and responsive controls", flush=True)
            if args.network_failures:
                print("PASS: bounded requests, network interruption recovery, failed-asset message and Retry action", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
