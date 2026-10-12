# Jensen 2M example

[Play the scene](https://opsiclear-4dgs.github.io/ftgs-player/?example=jensen-2m)
or [download the TSOG](https://opsiclear-4dgs.github.io/ftgs-player/examples/assets/jensen-2m.tsog).
The demo loads all 2,000,000 Gaussians and uses the saved front-view camera.
The website fetches this file only when the example is selected.

`jensen-2m.tsog` is the unchanged reconstruction from
[sam3dbx4danyone](https://github.com/OpsiClear-4DGS/sam3dbx4danyone):
the Base36 Jensen 2M run with original 1M movement scales, fitting seed 2042.
It contains 121 source timestamps at 24 fps, 5 seconds of animated content,
and the original embedded audio track. The ZIP container is 45,106,423 bytes
(45.1 MB). The detailed provenance, SHA-256 and camera bookmark are in
[jensen-2m.json](jensen-2m.json).

This is an example reconstruction from generated multiview inputs, not a
reference mesh or a claim of accurate recovered geometry. It is kept separately
from the synthetic decoder fixtures and excluded from the reusable npm package.

The AGPL-3.0-only license covers the player code. Source media and embedded audio
retain their original rights; the code license does not relicense that content.

## Social preview

`jensen-preview.mp4` is a five-second, 24 fps render of the same full 2M scene
and saved camera, encoded as 960×540 H.264 with AAC source audio. It is the
linear video used by the X Player Card, not an interactive TSOG player.
`site/assets/social-preview.jpg` is a 1200×675 render at normalized time 0.3.
The preview and its audio retain the source media's original rights.

Regenerate both from the unchanged retained TSOG using Chromium and ffmpeg:

```bash
python -m pip install -r tests/requirements.txt
python -m playwright install chromium
python tools/render-social-preview.py
```

The tool waits for the renderer to finish each requested timestamp before
capturing it, and restores the saved camera. The JPEG, video and dedicated
`examples/social-player.html` are served as static files; the social card
requires no WebGL decoding or model download.
