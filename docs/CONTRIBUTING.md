# Development

The reusable API lives in `src/`; it must not import website markup or styles
from `site/`. Keep the root `player.js`, `embed.js` and `index.js` entry points
working for existing browser integrations. `src/sort-worker.js` and
`src/decode-worker.js` must remain available with their imported modules in
packages and static builds.

Run the unit, package and retained-example checks with Node.js 22+:

```bash
npm test
npm run validate:example
npm run build
npm pack --dry-run
```

Browser checks use optional Python test dependencies:

```bash
python -m pip install -r tests/requirements.txt
python -m playwright install chromium
python tests/browser_smoke.py
python tests/browser_api.py
python tests/browser_tsog.py
python tests/browser_workers.py
python tests/browser_audio.py
python tests/browser_xr.py
python tests/browser_sandbox.py
python tests/browser_project.py
python tests/browser_project.py --network-failures
```

The first five checks cover rendering, navigation, canvas/iframe isolation,
cross-origin commands, cancellation/cleanup, decoder conformance, audio and
simulated XR. `browser_project.py` verifies the built site under a GitHub Pages
prefix and the real Jensen example with all 2M points, audio, playback and
scrubbing. `--network-failures` verifies bounded range requests, automatic
retries and user recovery after an interrupted download. Pass
`--browser /path/to/chromium` to use an existing browser.
`browser_sandbox.py` checks rendering, audio after Play, the built-in controls
and cleanup in cross-origin and opaque-origin iframes. This verifies browser
compatibility; X card acceptance requires a real post and testing in X clients.
Actual device AR support and performance still need physical-device testing.

To profile loading with all example points, excluding network time from decoding:

```bash
python tools/benchmark-loading.py --output /tmp/loading.json --capture
```

Run with `--compare /tmp/baseline.json` after changing the decoder or renderer
to require identical attribute and rendered-frame hashes. The benchmark uses
headless Chromium with software WebGL; see [PERFORMANCE.md](PERFORMANCE.md) for
the measured stages and limits. Keep large benchmark artifacts outside the repo.

Keep synthetic fixtures reproducible; do not replace them with a training
result. New recorded examples need provenance, a checksum and their original
media attribution. `examples/assets/jensen-2m.tsog` is intentionally retained
in Git and intentionally omitted from the npm library archive.

GitHub Pages serves the `main` branch root; `dist/` can also be deployed to any
static host. Npm registry publication is not configured. Preserve AGPL-3.0-only
and third-party notices.

An optional GitHub Actions template is in `tools/ci/player-checks.yml`. Copy it
to `.github/workflows/player-checks.yml` to run the checks above on pushes and
pull requests. Creating workflows requires a GitHub credential with `workflow`
permission; the template is not active in this repository.
