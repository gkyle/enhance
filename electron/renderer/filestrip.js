// File strip: thumbnails for the base file and every generated output file,
// ported from the Qt FileStrip. Clicking a thumbnail makes it the active file
// (operation target + operations panel) and loads it as a compare; output files
// can be deleted from a hover control. Thumbnails reuse the /preview endpoint at
// a small size and refresh when a file's backing path changes.

(function () {
  const THUMB = 96;

  class FileStrip {
    constructor(container, state) {
      this.container = container;
      this.state = state;
      this.onSelect = null; // (fileInfo) => void
      this.onDelete = null; // (fileInfo) => void
      this.onSave = null; // (fileInfo) => void
      this._els = new Map(); // id -> { root, img, badges }
      state.onFilesChange(() => this.render());
    }

    async _thumbUrl(file) {
      if (file._thumbUrl && file._thumbPath === file.path) return file._thumbUrl;
      const preview = await window.api.getPreview(file.id, THUMB, THUMB);
      file._thumbUrl = window.api.assetUrl(preview.url);
      file._thumbPath = file.path;
      return file._thumbUrl;
    }

    render() {
      const state = this.state;
      const files = state.listFiles();
      // Order: base first, then the rest in insertion order.
      files.sort((a, b) => (a.kind === "base" ? -1 : b.kind === "base" ? 1 : 0));

      const seen = new Set();
      this.container.innerHTML = "";
      this._els.clear();

      for (const file of files) {
        seen.add(file.id);
        const root = document.createElement("div");
        root.className = "file-btn";
        if (file === state.active) root.classList.add("active");

        const img = document.createElement("img");
        img.className = "file-thumb";
        img.alt = file.basename || file.id;
        this._thumbUrl(file)
          .then((url) => (img.src = url))
          .catch(() => {});
        root.appendChild(img);

        const badges = document.createElement("div");
        badges.className = "file-badges";
        if (file.kind === "base") {
          const b = document.createElement("span");
          b.className = "badge base";
          b.textContent = "BASE";
          badges.appendChild(b);
        }
        const cmpIdx = state.compares.findIndex((c) => c && c.id === file.id);
        if (cmpIdx >= 0) {
          const b = document.createElement("span");
          b.className = "badge cmp";
          b.textContent = String(cmpIdx + 1);
          badges.appendChild(b);
        }
        if (file.kind === "output" && !file.saved) {
          const b = document.createElement("span");
          b.className = "badge unsaved";
          b.textContent = "•";
          b.title = "Unsaved";
          badges.appendChild(b);
        }
        root.appendChild(badges);

        const label = document.createElement("div");
        label.className = "file-label";
        label.textContent = file.basename || file.id;
        label.title = file.basename || file.id;
        root.appendChild(label);

        if (file.kind === "output") {
          const del = document.createElement("button");
          del.className = "file-del";
          del.textContent = "×";
          del.title = "Delete";
          del.addEventListener("click", (e) => {
            e.stopPropagation();
            if (this.onDelete) this.onDelete(file);
          });
          root.appendChild(del);

          if (!file.saved) {
            const save = document.createElement("button");
            save.className = "file-save";
            save.textContent = "💾";
            save.title = "Save…";
            save.addEventListener("click", (e) => {
              e.stopPropagation();
              if (this.onSave) this.onSave(file);
            });
            root.appendChild(save);
          }
        }

        root.addEventListener("click", () => {
          if (this.onSelect) this.onSelect(file);
        });

        this.container.appendChild(root);
        this._els.set(file.id, { root, img, badges });
      }
    }
  }

  window.FileStrip = FileStrip;
})();
