// Selection + preview state — the renderer-side equivalent of SelectionManager.
// Holds the base file, up to 3 compare files, the active file (operation target),
// the render mode, and a canonical registry of FileInfo objects keyed by id so a
// single object per file is shared across base/compares/active and the file strip.
// Decoded previews are cached on each FileInfo as an ImageBitmap and reloaded when
// a file's path changes (e.g. after a strength re-blend or a chained operation).

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
      this.active = null; // FileInfo whose operations panel is shown / run target
      this.renderMode = RenderMode.Single;
      this._byId = new Map(); // id -> canonical FileInfo
      this._listeners = [];
      this._fileListeners = [];
      // Detected masks on the base file, with their overlay bitmaps and which
      // are currently drawn on the canvas.
      this.masks = []; // [{index,label,uniqueLabel,box,overlayUrl,bitmap}]
      this.visibleMaskIndices = new Set();
      this._maskListeners = [];
    }

    onChange(fn) {
      this._listeners.push(fn);
    }

    // Fired when the set of files or the active/selection changes (for the strip).
    onFilesChange(fn) {
      this._fileListeners.push(fn);
    }

    // Fired when the mask list or their visibility changes.
    onMasksChange(fn) {
      this._maskListeners.push(fn);
    }

    _notify() {
      this._listeners.forEach((fn) => fn(this));
    }

    _notifyFiles() {
      this._fileListeners.forEach((fn) => fn(this));
    }

    _notifyMasks() {
      this._maskListeners.forEach((fn) => fn(this));
    }

    // Return the canonical FileInfo for an id, updating it in place if it already
    // exists. When the backing path changes, drop the cached bitmap so the next
    // load re-fetches the (now different) preview.
    ingest(info) {
      const existing = this._byId.get(info.id);
      if (!existing) {
        this._byId.set(info.id, info);
        return info;
      }
      const pathChanged = existing.path !== info.path;
      existing.kind = info.kind;
      existing.basename = info.basename;
      existing.path = info.path;
      existing.width = info.width;
      existing.height = info.height;
      existing.bitDepth = info.bitDepth;
      existing.saved = info.saved;
      existing.operations = info.operations || [];
      if (pathChanged) {
        existing.bitmap = null;
        existing.previewWidth = null;
        existing.previewHeight = null;
      }
      return existing;
    }

    getFile(id) {
      return this._byId.get(id) || null;
    }

    listFiles() {
      return Array.from(this._byId.values());
    }

    async setBase(fileInfo) {
      this.base = await loadBitmap(this.ingest(fileInfo));
      if (this.active === null) this.active = this.base;
      this._notify();
      this._notifyFiles();
    }

    async setCompare(index, fileInfo) {
      this.compares[index] = fileInfo
        ? await loadBitmap(this.ingest(fileInfo))
        : null;
      this._notify();
      this._notifyFiles();
    }

    // Assign to the first free compare slot; returns the slot index or -1.
    async addCompare(fileInfo) {
      const canonical = this.ingest(fileInfo);
      const existingIdx = this.compares.findIndex(
        (c) => c && c.id === canonical.id
      );
      if (existingIdx >= 0) {
        await loadBitmap(canonical);
        this._notify();
        this._notifyFiles();
        return existingIdx;
      }
      const idx = this.compares.findIndex((c) => c === null);
      if (idx < 0) return -1;
      await this.setCompare(idx, canonical);
      return idx;
    }

    getCompare(index) {
      return this.compares[index] || null;
    }

    setActive(fileInfo) {
      this.active = fileInfo ? this.ingest(fileInfo) : null;
      this._notifyFiles();
    }

    setRenderMode(mode) {
      this.renderMode = mode;
      this._notify();
    }

    // Register/update a file after a run or strength change: refresh metadata,
    // reload its preview if the path changed, and repaint any view showing it.
    async updateFile(fileInfo) {
      const canonical = this.ingest(fileInfo);
      await loadBitmap(canonical);
      this._notify();
      this._notifyFiles();
      return canonical;
    }

    removeFile(id) {
      const file = this._byId.get(id);
      this._byId.delete(id);
      if (this.base === file) this.base = null;
      if (this.active === file) this.active = this.base;
      this.compares = this.compares.map((c) => (c === file ? null : c));
      this._notify();
      this._notifyFiles();
    }

    // Load mask metadata (from GET /masks) and decode each overlay bitmap so the
    // canvas can composite visible ones over the base image.
    async setMasks(maskInfos) {
      const masks = [];
      for (const info of maskInfos || []) {
        let bitmap = null;
        if (info.overlayUrl) {
          try {
            const res = await fetch(window.api.assetUrl(info.overlayUrl));
            bitmap = await createImageBitmap(await res.blob());
          } catch (e) {
            bitmap = null;
          }
        }
        masks.push({ ...info, bitmap });
      }
      this.masks = masks;
      // Hide all by default (matches the Qt automask flow).
      this.visibleMaskIndices = new Set();
      this._notifyMasks();
      this._notify();
    }

    setMaskVisible(index, visible) {
      if (visible) this.visibleMaskIndices.add(index);
      else this.visibleMaskIndices.delete(index);
      this._notifyMasks();
      this._notify();
    }

    setAllMasksVisible(visible) {
      this.visibleMaskIndices = visible
        ? new Set(this.masks.map((m) => m.index))
        : new Set();
      this._notifyMasks();
      this._notify();
    }

    clear() {
      this.base = null;
      this.compares = [null, null, null];
      this.active = null;
      this.renderMode = RenderMode.Single;
      this._byId.clear();
      this.masks = [];
      this.visibleMaskIndices = new Set();
      this._notify();
      this._notifyFiles();
      this._notifyMasks();
    }
  }

  window.RenderMode = RenderMode;
  window.selectionState = new SelectionState();
})();
