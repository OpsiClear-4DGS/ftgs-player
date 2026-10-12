# Website design

The standalone player and embedding examples follow
[COLMAPView's design system](https://github.com/ColmapView/Colmapview.github.io/blob/main/docs/design-system.md)
and [style reference](https://github.com/ColmapView/Colmapview.github.io/blob/main/STYLE_REFERENCE.md).
The shared tokens live in `site/theme.css`: neutral charcoal surfaces, silver
accents, a 4 px spacing scale, restrained borders and 4–6 px corner radii.

The website has a single opening panel for local files and the Jensen example.
During playback only the scene and a compact icon toolbar remain. The toolbar
fades while playing, stays available on hover or keyboard focus, and uses
44 px controls on small screens. There is no persistent title bar or sidebar.

IBM Plex Sans and JetBrains Mono are self-hosted; their SIL Open Font License
notices are in `site/fonts/`. Icons are inline SVG. No external fonts, icon
services or UI framework are required at runtime.

The canvas library never imports these styles. Hosts can use this theme or
provide their own. `examples/embedding.html` demonstrates host-owned controls
for both the canvas library and the iframe API.
