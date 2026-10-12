import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { createHash } from "node:crypto";
import { FTGSPlayer, FTGSEmbed, PLAYER_EVENTS } from "@opsiclear/ftgs-player";
import { FTGSPlayer as legacyPlayer } from "../player.js";
import { FTGSEmbed as legacyEmbed } from "../embed.js";
import { openZip } from "../src/zip.js";

test("package and stable browser entry points share the same controller classes", () => {
  assert.equal(FTGSPlayer, legacyPlayer);
  assert.equal(FTGSEmbed, legacyEmbed);
  assert.ok(PLAYER_EVENTS.includes("destroy"));
  assert.ok(PLAYER_EVENTS.includes("audiochange"));
});

test("reusable package includes its worker and licenses, and excludes recorded demo data", async () => {
  const { stdout } = await promisify(execFile)("npm", ["pack", "--dry-run", "--json"], {
    cwd: new URL("../", import.meta.url), maxBuffer: 4 * 1024 * 1024,
  });
  const pack = JSON.parse(stdout)[0];
  const paths = new Set(pack.files.map((file) => file.path));
  for (const path of ["src/index.js", "src/player.js", "src/embed.js", "src/sort-worker.js",
                      "src/tsog.js", "src/webp.js", "LICENSE", "docs/THIRD_PARTY.md", "docs/API.md"])
    assert.ok(paths.has(path), `missing ${path}`);
  assert.ok(![...paths].some((path) => /^(examples|tests|site|dist)\//.test(path)));
  assert.ok(pack.size < 1024 * 1024, "package unexpectedly includes model data");
});

test("retained Jensen example matches its provenance and preserves 2M rows and audio", async () => {
  const folder = new URL("../examples/assets/", import.meta.url);
  const metadata = JSON.parse(await readFile(new URL("jensen-2m.json", folder)));
  const data = await readFile(new URL(metadata.file, folder));
  assert.equal(data.byteLength, metadata.bytes);
  assert.equal(createHash("sha256").update(data).digest("hex"), metadata.sha256);
  const archive = await openZip(new Blob([data]));
  const model = JSON.parse(new TextDecoder().decode(await archive.read("meta.json")));
  assert.equal(model.count, 2000000);
  assert.equal(model.playback.fps, metadata.fps);
  assert.equal(model.playback.duration, metadata.duration);
  assert.ok(model.audio.file);
  assert.ok((await archive.read(model.audio.file)).byteLength > 0);
});
