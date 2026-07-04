// Renderer wiring: open base/compare images, switch render modes, zoom menu,
// and live GPU stats. Drives the canvas Viewer via selectionState.

(function () {
  const RenderMode = window.RenderMode;
  const state = window.selectionState;

  const els = {
    open: document.getElementById("btnOpen"),
    add: document.getElementById("btnAdd"),
    sharpen: document.getElementById("btnSharpen"),
    denoise: document.getElementById("btnDenoise"),
    upscale: document.getElementById("btnUpscale"),
    single: document.getElementById("btnSingle"),
    split: document.getElementById("btnSplit"),
    grid: document.getElementById("btnGrid"),
    zoom: document.getElementById("btnZoom"),
    zoomMenu: document.getElementById("zoomMenu"),
    filename: document.getElementById("filename"),
    gpu: document.getElementById("gpu"),
    placeholder: document.getElementById("placeholder"),
    compareInfo: document.getElementById("compareInfo"),
    canvas: document.getElementById("canvas"),
    progress: document.getElementById("progress"),
    progressLabel: document.getElementById("progressLabel"),
    progressBar: document.getElementById("progressBar"),
    cancel: document.getElementById("btnCancel"),
  };

  const viewer = new window.Viewer(els.canvas, state);
  viewer.onZoomChange = (z) => {
    els.zoom.textContent = `${Math.round(z * 100)}%`;
  };

  function setModeButtons(mode) {
    [els.single, els.split, els.grid].forEach((b) => b.classList.remove("active"));
    if (mode === RenderMode.Single) els.single.classList.add("active");
    if (mode === RenderMode.Split) els.split.classList.add("active");
    if (mode === RenderMode.Grid) els.grid.classList.add("active");
  }

  function enableViewerControls() {
    [els.add, els.sharpen, els.denoise, els.upscale, els.single, els.split, els.grid, els.zoom].forEach(
      (b) => (b.disabled = false)
    );
    els.placeholder.style.display = "none";
  }

  function updateCompareInfo() {
    const names = state.compares
      .map((c, i) => (c ? `${i + 1}: ${c.basename}` : null))
      .filter(Boolean);
    els.compareInfo.textContent = names.length
      ? `Compare — ${names.join("   ")}`
      : "";
  }

  // ----- open / add -----
  els.open.addEventListener("click", async () => {
    const path = await window.native.openImage();
    if (!path) return;
    const info = await window.api.setBaseFile(path);
    els.filename.textContent = info.basename || path;
    els.filename.classList.remove("muted");
    await state.setBase(info);
    enableViewerControls();
    updateCompareInfo();
  });

  els.add.addEventListener("click", async () => {
    const path = await window.native.openImage();
    if (!path) return;
    const info = await window.api.appendFile(path);
    const idx = await state.addCompare(info);
    if (idx < 0) {
      els.compareInfo.textContent = "Compare slots full (max 3)";
      return;
    }
    updateCompareInfo();
  });

  // ----- render modes -----
  els.single.addEventListener("click", () => {
    setModeButtons(RenderMode.Single);
    state.setRenderMode(RenderMode.Single);
  });
  els.split.addEventListener("click", () => {
    setModeButtons(RenderMode.Split);
    state.setRenderMode(RenderMode.Split);
  });
  els.grid.addEventListener("click", () => {
    setModeButtons(RenderMode.Grid);
    state.setRenderMode(RenderMode.Grid);
  });

  // ----- zoom menu -----
  els.zoom.addEventListener("click", (e) => {
    e.stopPropagation();
    els.zoomMenu.classList.toggle("hidden");
  });
  els.zoomMenu.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", () => {
      viewer.setZoomFactor(b.dataset.zoom);
      els.zoomMenu.classList.add("hidden");
    });
  });
  document.addEventListener("click", () => els.zoomMenu.classList.add("hidden"));

  // ----- run pipeline -----
  // Queue of pending jobIds for this batch, and a flag to auto-compare the first
  // completed output (matches the Qt "switch to side-by-side on completion").
  const pendingJobs = new Set();
  let autoCompareDone = false;

  function showProgress(label, indeterminate) {
    els.progress.classList.remove("hidden");
    els.progressLabel.textContent = label;
    els.progressBar.classList.toggle("indeterminate", !!indeterminate);
    if (indeterminate) els.progressBar.style.width = "";
    else els.progressBar.style.width = "0%";
  }

  function hideProgress() {
    els.progress.classList.add("hidden");
  }

  async function runOperation(operation) {
    if (!state.base) return;
    const params = await window.openModelDialog(operation);
    if (!params) return;

    autoCompareDone = false;
    // Run each selected model in sequence (backend job queue serializes them).
    for (const modelKey of params.models) {
      const { jobId } = await window.api.runModel({
        fileId: "base",
        modelKey,
        operation: params.operation,
        tileSize: params.tileSize,
        tilePadding: params.tilePadding,
        maintainScale: params.maintainScale,
        device: params.device === "cpu" ? null : params.device,
      });
      pendingJobs.add(jobId);
    }
    showProgress(`${operation} queued…`, true);
  }

  els.sharpen.addEventListener("click", () => runOperation("sharpen"));
  els.denoise.addEventListener("click", () => runOperation("denoise"));
  els.upscale.addEventListener("click", () => runOperation("upscale"));
  els.cancel.addEventListener("click", () => window.api.interrupt().catch(() => {}));

  window.api.on("progress", (p) => {
    if (!pendingJobs.has(p.jobId)) return;
    if (p.statusMessage) {
      showProgress(p.statusMessage, true);
    } else if (p.total) {
      els.progress.classList.remove("hidden");
      els.progressBar.classList.remove("indeterminate");
      els.progressLabel.textContent = `Processing ${p.count}/${p.total}`;
      els.progressBar.style.width = `${Math.round((p.count / p.total) * 100)}%`;
    }
  });

  window.api.on("runComplete", async (payload) => {
    pendingJobs.delete(payload.jobId);
    // Add the output as a compare file; switch to side-by-side for the first one.
    const idx = await state.addCompare(payload.file);
    if (idx === 0 && !autoCompareDone) {
      autoCompareDone = true;
      setModeButtons(RenderMode.Split);
      state.setRenderMode(RenderMode.Split);
    }
    updateCompareInfo();
    if (pendingJobs.size === 0) hideProgress();
  });

  window.api.on("runError", (payload) => {
    pendingJobs.delete(payload.jobId);
    els.compareInfo.textContent = `Run failed: ${payload.message}`;
    if (pendingJobs.size === 0) hideProgress();
  });

  // ----- GPU stats -----
  function renderGpu(stats) {
    if (!stats || !stats.present) {
      els.gpu.textContent = "GPU: none";
      return;
    }
    const parts = [];
    if (stats.utilization != null) parts.push(`${Math.round(stats.utilization * 100)}%`);
    if (stats.memoryTotalGb != null && stats.memoryAvailableGb != null) {
      const used = stats.memoryTotalGb - stats.memoryAvailableGb;
      parts.push(`${used.toFixed(1)}/${stats.memoryTotalGb.toFixed(1)}GB`);
    }
    els.gpu.textContent = `GPU: ${parts.join("  ") || stats.preferredDevice}`;
  }

  window.api.on("gpuStats", renderGpu);
  window.api.connectWebSocket();
  window.api.getGpu().then(renderGpu).catch(() => {});
})();
