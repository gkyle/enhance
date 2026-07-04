// Selection + preview state — the renderer-side equivalent of SelectionManager.
// Holds the base file and up to 3 compare files, the render mode, and a cache of
// decoded preview ImageBitmaps (fetched full-res once, then scaled client-side).

(function () {
  const RenderMode = { Single: "single", Split: "split", Grid: "grid" };

  async function loadBitmap(fileInfo) {
    // Fetch the full-res 8-bit preview once and decode it to an ImageBitmap.
    if (fileInfo.bitmap) return fileInfo;
    const preview = await window.api.getPreview(fileInfo.id);
    const res = await fetch(window.api.assetUrl(preview.url));
    const blob = await res.blob();
    fileInfo.bitmap = await createImageBitmap(blob);
    // Preview dimensions are the display dimensions (may differ if downscaled).
    fileInfo.previewWidth = preview.width;
    fileInfo.previewHeight = preview.height;
    return fileInfo;
  }

  class SelectionState {
    constructor() {
      this.base = null; // FileInfo (+bitmap) or null
      this.compares = [null, null, null];
      this.renderMode = RenderMode.Single;
      this._listeners = [];
    }

    onChange(fn) {
      this._listeners.push(fn);
    }

    _notify() {
      this._listeners.forEach((fn) => fn(this));
    }

    async setBase(fileInfo) {
      this.base = await loadBitmap(fileInfo);
      this._notify();
    }

    async setCompare(index, fileInfo) {
      this.compares[index] = fileInfo ? await loadBitmap(fileInfo) : null;
      this._notify();
    }

    // Assign to the first free compare slot; returns the slot index or -1.
    async addCompare(fileInfo) {
      const idx = this.compares.findIndex((c) => c === null);
      if (idx < 0) return -1;
      await this.setCompare(idx, fileInfo);
      return idx;
    }

    getCompare(index) {
      return this.compares[index] || null;
    }

    setRenderMode(mode) {
      this.renderMode = mode;
      this._notify();
    }

    clear() {
      this.base = null;
      this.compares = [null, null, null];
      this.renderMode = RenderMode.Single;
      this._notify();
    }
  }

  window.RenderMode = RenderMode;
  window.selectionState = new SelectionState();
})();
