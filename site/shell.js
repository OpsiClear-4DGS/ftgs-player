/** The standalone website UI; importing the canvas library adds no markup. */
export function mountPlayerShell(viewer) {
  viewer.innerHTML = `
    <svg class="symbols" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <symbol id="play" viewBox="0 0 24 24"><path d="M8 5.5v13l10-6.5Z" /></symbol>
        <symbol id="pause" viewBox="0 0 24 24"><path d="M7 5.5h3.5v13H7zm6.5 0H17v13h-3.5z" /></symbol>
        <symbol id="sound" viewBox="0 0 24 24"><path d="M11 5 6 9H3v6h3l5 4ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14" /></symbol>
        <symbol id="silent" viewBox="0 0 24 24"><path d="M11 5 6 9H3v6h3l5 4Zm5 4 5 6m0-6-5 6" /></symbol>
        <symbol id="open" viewBox="0 0 24 24"><path d="M3 7.5V5.8c0-.7.6-1.3 1.3-1.3H10l2 2H20v3M3 9.5h18l-2.5 10H4.3L3 9.5Z" /></symbol>
        <symbol id="reset" viewBox="0 0 24 24"><path d="M4.5 10a7.5 7.5 0 1 1 1.7 7M4.5 4.5V10H10" /></symbol>
        <symbol id="expand" viewBox="0 0 24 24"><path d="M8.5 4.5h-4v4m11-4h4v4m-15 7v4h4m11-4v4h-4" /></symbol>
        <symbol id="collapse" viewBox="0 0 24 24"><path d="M4.5 8.5h4v-4m7 0v4h4m-15 7h4v4m7 0v-4h4" /></symbol>
        <symbol id="add" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></symbol>
        <symbol id="code" viewBox="0 0 24 24"><path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16" /></symbol>
        <symbol id="source" viewBox="0 0 24 24"><path d="M9 19c-4 1-4-2-6-2m12 4v-3.4a3 3 0 0 0-.8-2.3c2.7-.3 5.5-1.3 5.5-6a4.7 4.7 0 0 0-1.3-3.3 4.4 4.4 0 0 0-.1-3.3s-1-.3-3.4 1.3a11.4 11.4 0 0 0-6.2 0C6.3 2.4 5.3 2.7 5.3 2.7a4.4 4.4 0 0 0-.1 3.3 4.7 4.7 0 0 0-1.3 3.3c0 4.7 2.8 5.7 5.5 6a3 3 0 0 0-.8 2.3V21" /></symbol>
      </defs>
    </svg>
    <canvas id="canvas" tabindex="0" aria-label="3D scene. Drag to orbit, Shift-drag to pan, scroll to zoom. WASD to move, Q/E down/up, Shift to move faster."></canvas>
    <section id="welcome" class="welcome" aria-labelledby="welcome-title">
      <div class="welcome-heading">
        <h1 id="welcome-title">FTGS Player</h1>
        <nav id="welcome-links" aria-label="Player resources">
          <a class="icon-button" href="./examples/embedding.html" aria-label="Embedding examples" title="Embedding examples"><svg aria-hidden="true"><use href="#code" /></svg></a>
          <a class="icon-button" href="https://github.com/OpsiClear-4DGS/ftgs-player" aria-label="Source code" title="Source code"><svg aria-hidden="true"><use href="#source" /></svg></a>
        </nav>
      </div>
      <button id="empty" class="empty" aria-label="Choose a .ftgs.ply or .tsog file">
        <svg class="empty-icon" aria-hidden="true"><use href="#add" /></svg>
        <span class="empty-title">Open a 4D scene</span>
        <span class="empty-caption">Drop a .tsog or .ftgs.ply file, or click to browse</span>
      </button>
      <div class="welcome-actions">
        <a class="button example-link" href="?example=jensen-2m"><svg aria-hidden="true"><use href="#play" /></svg>Try Jensen <span>2M · 45 MB</span></a>
        <a class="license-link" href="./LICENSE">AGPL-3.0</a>
      </div>
    </section>
    <input id="file" type="file" accept=".ply,.tsog" hidden aria-label="Open splat file" />
    <div id="message" class="message" role="status" hidden><span id="message-text"></span><button id="retry-example" class="button" hidden>Retry</button></div>
    <div id="ar-hint" class="message ar-hint" role="status" hidden></div>
    <div id="drop-hint" class="drop-hint" hidden>
      <svg aria-hidden="true"><use href="#open" /></svg><span>Drop to play</span>
    </div>
    <div id="controls" class="controls" role="group" aria-label="Playback controls" hidden>
      <div id="timeline-area" class="timeline-area">
        <output id="seek-preview" class="seek-preview" aria-hidden="true">0:00</output>
        <input id="timeline" type="range" min="0" max="1" step="0.0001" value="0" aria-label="Timeline" disabled />
      </div>
      <div class="transport">
        <button id="play-toggle" class="icon-button" data-tooltip="Play (Space)" aria-label="Play" disabled>
          <svg class="solid-icon" aria-hidden="true"><use id="play-icon" href="#play" /></svg>
        </button>
        <div id="audio-controls" class="audio-controls" hidden>
          <button id="mute-toggle" class="icon-button" data-tooltip="Mute (M)" aria-label="Mute" aria-pressed="false">
            <svg aria-hidden="true"><use id="audio-icon" href="#sound" /></svg>
          </button>
          <input id="volume" type="range" min="0" max="1" step="0.01" value="1" aria-label="Volume" />
        </div>
        <output id="timecode" aria-label="Playback time" aria-live="off">0:00 <span>/ 0:00</span></output>
        <span class="transport-space"></span>
        <select id="playback-rate" class="playback-rate" aria-label="Playback speed" title="Playback speed" disabled>
          <option value="0.25">0.25×</option><option value="0.5">0.5×</option>
          <option value="0.75">0.75×</option><option value="1" selected>1×</option>
          <option value="1.25">1.25×</option><option value="1.5">1.5×</option>
          <option value="2">2×</option><option value="3">3×</option><option value="4">4×</option>
        </select>
        <button id="reset-view" class="icon-button" data-tooltip="Reset view (R)" aria-label="Reset view" disabled>
          <svg aria-hidden="true"><use href="#reset" /></svg>
        </button>
        <button id="open-file" class="icon-button" data-tooltip="Open file (O)" aria-label="Open file">
          <svg aria-hidden="true"><use href="#open" /></svg>
        </button>
        <button id="ar" class="icon-button ar-button" data-tooltip="View in AR" aria-label="View in AR" aria-pressed="false" disabled hidden>AR</button>
        <button id="fullscreen" class="icon-button" data-tooltip="Fullscreen (F)" aria-label="Fullscreen">
          <svg aria-hidden="true"><use id="fullscreen-icon" href="#expand" /></svg>
        </button>
      </div>
    </div>`;
}
