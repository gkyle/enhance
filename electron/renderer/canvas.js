// Canvas viewer — ports CanvasLabel's pan/zoom/split/grid geometry to <canvas>.
// Preview bitmaps are fetched full-res once (in state.js); all pan/zoom/split math
// runs client-side here, mirroring how showFiles() worked in the Qt app.

(function () {
  const RenderMode = window.RenderMode;

  class Viewer {
    constructor(canvas, state) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.state = state;
      this.onZoomChange = null;

      this.zoom = 1.0;
      this.posX = 0;
      this.posY = 0;
      this.dragX = 0;
      this.dragY = 0;
      this.mouseX = 0;
      this.mouseY = 0;
      this.fraction = 0.5;

      state.onChange(() => this.onStateChange());
      this._bindEvents();
      window.addEventListener("resize", () => this._resizeAndPaint());
      this._resizeBackingStore();
    }

    // ----- geometry helpers (logical CSS pixels) -----
    width() {
      return this.canvas.clientWidth;
    }
    height() {
      return this.canvas.clientHeight;
    }
    base() {
      return this.state.base;
    }
    isGrid() {
      return this.state.renderMode === RenderMode.Grid;
    }

    fitWidth() {
      let lw = this.width();
      if (this.isGrid()) lw = lw / 2;
      return lw / this.base().previewWidth;
    }
    fitHeight() {
      let lh = this.height();
      if (this.isGrid()) lh = lh / 2;
      return lh / this.base().previewHeight;
    }
    fit() {
      return Math.min(this.fitWidth(), this.fitHeight());
    }

    // Effective per-image zoom: compare images are shown relative to the base's
    // scale (ports makeScaledPixmap's scale = img2.h / img1.h).
    effZoom(file) {
      if (!file || file === this.base()) return this.zoom;
      return (this.zoom * this.base().previewHeight) / file.previewHeight;
    }

    resetZoom(zoom, resetPosition = true) {
      if (resetPosition) {
        this.posX = 0;
        this.posY = 0;
      }
      this.zoom = zoom;
      this._emitZoom();
    }

    setZoom(dir, mx, my) {
      const old = this.zoom;
      if (dir < 0) this.zoom /= 1.1;
      if (dir > 0) this.zoom *= 1.1;

      const base = this.base();
      if (!base) return;
      const iw = base.previewWidth;
      const ih = base.previewHeight;
      const lw = this.width();
      const lh = this.height();
      if (iw === 0 || ih === 0) return;

      const minZoom = this.isGrid()
        ? Math.min(lw / 2 / iw, lh / 2 / ih)
        : Math.min(lw / iw, lh / ih);
      if (this.zoom < minZoom) {
        this.zoom = minZoom;
        this.resetZoom(this.zoom);
      }

      if (this.isGrid()) {
        if (mx > this.width() / 2) mx = mx - this.width() / 2;
        if (my > this.height() / 2) my = my - this.height() / 2;
      }
      this.posX = mx - (mx - this.posX) * (this.zoom / old);
      this.posY = my - (my - this.posY) * (this.zoom / old);

      this.paint();
      this._emitZoom();
    }

    setZoomFactor(level) {
      if (!this.base()) return;
      if (level === "FIT") this.resetZoom(this.fit());
      else if (level === "FIT_WIDTH") this.resetZoom(this.fitWidth());
      else if (level === "FIT_HEIGHT") this.resetZoom(this.fitHeight());
      else if (typeof level === "string" && level.includes("%")) {
        const n = parseInt(level.replace("%", ""), 10);
        if (!Number.isNaN(n)) this.resetZoom(n / 100, false);
      }
      this.paint();
    }

    // Recenter if the image fits; clamp if panned out of bounds (ports
    // maybeClampImage). scale = 2 for grid quadrants.
    clampImage(scale = 1) {
      const base = this.base();
      const h = base.previewHeight * this.zoom;
      const w = base.previewWidth * this.zoom;
      const W = this.width() / scale;
      const H = this.height() / scale;

      if (w <= W) {
        this.posX = (W - base.previewWidth * this.zoom) / 2;
      } else if (this.posX > 0) {
        this.posX = 0;
      } else if (W - this.posX > w) {
        this.posX = W - w;
      }

      if (h <= H) {
        this.posY = (H - base.previewHeight * this.zoom) / 2;
      } else if (this.posY > 0) {
        this.posY = 0;
      } else if (H - this.posY > h) {
        this.posY = H - h;
      }
    }

    // ----- painting -----
    onStateChange() {
      if (this.base()) this.resetZoom(this.fit());
      this.paint();
    }

    _resizeBackingStore() {
      const dpr = window.devicePixelRatio || 1;
      this.canvas.width = Math.round(this.width() * dpr);
      this.canvas.height = Math.round(this.height() * dpr);
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    _resizeAndPaint() {
      this._resizeBackingStore();
      this.paint();
    }

    paint() {
      this._resizeBackingStore();
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.width(), this.height());
      if (!this.base() || !this.base().bitmap) return;

      const mode = this.state.renderMode;
      if (mode === RenderMode.Single) this._paintSingle();
      else if (mode === RenderMode.Split) this._paintSplit();
      else if (mode === RenderMode.Grid) this._paintGrid();
    }

    _drawImageIn(file, clipX, clipY, clipW, clipH, originX, originY) {
      const ctx = this.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.rect(clipX, clipY, clipW, clipH);
      ctx.clip();
      const eff = this.effZoom(file);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(
        file.bitmap,
        originX + this.posX,
        originY + this.posY,
        file.previewWidth * eff,
        file.previewHeight * eff
      );
      this._drawLabel(file, clipX, clipY, clipW, clipH);
      ctx.restore();
    }

    _drawLabel(file, x, y, w, h) {
      if (!file || !file.basename) return;
      const ctx = this.ctx;
      ctx.font = "12px Arial";
      ctx.fillStyle = "rgba(255,255,255,0.9)";
      ctx.textAlign = "right";
      ctx.textBaseline = "bottom";
      ctx.fillText(file.basename, x + w - 6, y + h - 6, w - 10);
    }

    _paintSingle() {
      this.clampImage(1);
      this._drawImageIn(this.base(), 0, 0, this.width(), this.height(), 0, 0);
    }

    _paintSplit() {
      const W = this.width();
      const H = this.height();
      this.clampImage(1);
      const padX = this.posX > 0 ? this.posX : 0;
      let splitX = W * this.fraction;
      if (splitX < padX) splitX = padX;
      if (splitX > W - padX) splitX = W - padX;

      this._drawImageIn(this.base(), 0, 0, splitX, H, 0, 0);

      const compare = this.state.getCompare(0);
      if (compare && compare.bitmap && splitX < W - padX) {
        this._drawImageIn(compare, splitX, 0, W - splitX, H, 0, 0);
      }

      const ctx = this.ctx;
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(splitX - 1, 0);
      ctx.lineTo(splitX - 1, H);
      ctx.stroke();
    }

    _paintGrid() {
      const W = this.width();
      const H = this.height();
      const qw = W / 2;
      const qh = H / 2;
      this.clampImage(2);

      const files = [
        this.base(),
        this.state.getCompare(0),
        this.state.getCompare(1),
        this.state.getCompare(2),
      ];
      const origins = [
        [0, 0],
        [qw, 0],
        [0, qh],
        [qw, qh],
      ];
      files.forEach((file, i) => {
        if (file && file.bitmap) {
          const [ox, oy] = origins[i];
          this._drawImageIn(file, ox, oy, qw, qh, ox, oy);
        }
      });

      const ctx = this.ctx;
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(qw - 1, 0);
      ctx.lineTo(qw - 1, H);
      ctx.moveTo(0, qh - 1);
      ctx.lineTo(W, qh - 1);
      ctx.stroke();
    }

    // ----- interaction -----
    _emitZoom() {
      if (this.onZoomChange) this.onZoomChange(this.zoom);
    }

    _bindEvents() {
      const c = this.canvas;
      c.addEventListener("wheel", (e) => {
        e.preventDefault();
        if (!this.base()) return;
        this.setZoom(-e.deltaY, this.mouseX, this.mouseY);
      });
      c.addEventListener("mousedown", (e) => {
        if (e.button === 0) {
          this.dragX = e.offsetX - this.posX;
          this.dragY = e.offsetY - this.posY;
        }
        if (e.button === 2 && this.state.renderMode === RenderMode.Split) {
          this.fraction = e.offsetX / this.width();
          this.paint();
        }
      });
      c.addEventListener("mousemove", (e) => {
        this.mouseX = e.offsetX;
        this.mouseY = e.offsetY;
        if (e.buttons === 1) {
          this.posX = e.offsetX - this.dragX;
          this.posY = e.offsetY - this.dragY;
          this.paint();
        } else if (e.buttons === 2 && this.state.renderMode === RenderMode.Split) {
          this.fraction = Math.min(1, Math.max(0, e.offsetX / this.width()));
          this.paint();
        }
      });
      c.addEventListener("dblclick", () => {
        if (!this.base()) return;
        this.resetZoom(this.fit());
        this.paint();
      });
      c.addEventListener("contextmenu", (e) => e.preventDefault());
    }
  }

  window.Viewer = Viewer;
})();
