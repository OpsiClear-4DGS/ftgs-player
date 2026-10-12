"""Render the retained 4D scene into the social card's JPEG and MP4 assets."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import zipfile

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Existing Chromium executable")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / "examples/assets/jensen-2m.json").read_text())
    scene = root / "examples/assets/jensen-2m.tsog"
    if not scene.is_file():
        parser.error("Run this tool in the standalone repository with the retained TSOG")
    if not shutil.which("ffmpeg"):
        parser.error("ffmpeg is required")

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            if self.path == "/capture.html":
                body = b'''<!doctype html><html><head><link rel="icon" href="data:,">
                  <style>body{margin:0;background:#0a0a0a}canvas{display:block;width:100vw;height:100vh}</style>
                  </head><body><canvas id="scene"></canvas></body></html>'''
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="ftgs-social-") as directory:
            temporary = Path(directory)
            with zipfile.ZipFile(scene) as archive:
                model = json.loads(archive.read("meta.json"))
                audio_name = model["audio"]["file"]
                audio = temporary / ("audio" + Path(audio_name).suffix)
                audio.write_bytes(archive.read(audio_name))
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=args.browser, headless=True, args=[
                    "--no-sandbox", "--use-angle=swiftshader", "--enable-webgl",
                    "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-dev-shm-usage",
                ])
                page = browser.new_page(viewport={"width": 960, "height": 540})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/capture.html")
                page.evaluate('''async view => {
                  const { SplatRenderer } = await import('./src/renderer.js');
                  const draw = SplatRenderer.prototype.draw;
                  window.rendered = { count: 0, time: null };
                  SplatRenderer.prototype.draw = function(order, camera, time, ...rest) {
                    draw.call(this, order, camera, time, ...rest);
                    document.querySelector('canvas').getContext('webgl2').finish();
                    window.rendered = { count: window.rendered.count + 1, time };
                  };
                  const { FTGSPlayer } = await import('./src/index.js');
                  window.player = new FTGSPlayer(document.querySelector('canvas'), {
                    maxPoints: Infinity, autoplay: false, muted: true,
                  });
                  await player.load('./examples/assets/jensen-2m.tsog', {view});
                }''', metadata["view"])
                assert page.evaluate("player.state.pointCount") == metadata["points"]
                frames = round(metadata["duration"] * metadata["fps"])
                for index in range(frames):
                    time = index / frames
                    count = page.evaluate("window.rendered.count")
                    page.evaluate("time => player.seek(time)", time)
                    page.wait_for_function("target => rendered.count > target.count && rendered.time === target.time",
                                           arg={"count": count, "time": time}, timeout=30000)
                    page.locator("canvas").screenshot(path=temporary / f"frame-{index:04d}.png")
                    if (index + 1) % metadata["fps"] == 0:
                        print(f"Rendered {index + 1}/{frames} frames", flush=True)
                page.set_viewport_size({"width": 1200, "height": 675})
                count = page.evaluate("window.rendered.count")
                page.evaluate("player.seek(.3)")
                page.wait_for_function("count => rendered.count > count && rendered.time === .3", arg=count)
                page.locator("canvas").screenshot(path=root / "site/assets/social-preview.jpg", type="jpeg", quality=90)
                assert not errors, errors
                page.evaluate("player.destroy()")
                browser.close()
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-framerate", str(metadata["fps"]), "-i", str(temporary / "frame-%04d.png"),
                "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-t", str(metadata["duration"]),
                "-movflags", "+faststart", str(root / "examples/assets/jensen-preview.mp4"),
            ], check=True)
            print("Saved 1200×675 poster and 960×540 H.264/AAC preview with source audio", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
