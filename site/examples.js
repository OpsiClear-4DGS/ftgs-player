const presets = Object.freeze({
  "jensen-2m": new URL("../examples/assets/jensen-2m.json", import.meta.url),
});

/** Example assets are fetched only after an explicit example selection. */
export async function readExample(id) {
  const metadataURL = presets[id];
  if (!metadataURL) throw new Error(`Unknown example: ${id}`);
  const response = await fetch(metadataURL);
  if (!response.ok) throw new Error(`Example request failed: HTTP ${response.status}.`);
  const metadata = await response.json();
  return { ...metadata, source: new URL(metadata.file, metadataURL) };
}
