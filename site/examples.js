import { downloadJSON, downloadFile } from "./download.js?v=2";

const presets = Object.freeze({
  "jensen-2m": new URL("../examples/assets/jensen-2m.json", import.meta.url),
});

/** Example assets are fetched only after an explicit example selection. */
export async function readExample(id, { signal } = {}) {
  const metadataURL = presets[id];
  if (!metadataURL) throw new Error(`Unknown example: ${id}`);
  const metadata = await downloadJSON(metadataURL, { signal });
  return { ...metadata, source: new URL(metadata.file, metadataURL) };
}

export function downloadExample(example, options) {
  return downloadFile(example.source, { ...options, bytes: example.bytes });
}
