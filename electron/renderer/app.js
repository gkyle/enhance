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
    opsList: document.getElementById("opsList"),
    filestrip: document.getElementById("filestripInner"),
    progress: document.getElementById("progress"),
    progressLabel: document.getElementById("progressLabel"),
    progressBar: document.getElementById("progressBar"),
    cancel: document.getElementById("btnCancel"),
  };

  const viewer = new window.Viewer(els.canvas, state);
  viewer.onZoomChange = (z) => {
    els.zoom.textContent = `${Math.round(z * 100)}%`;
  };

  const strip = new window.FileStrip(els.filestrip, state);
  const ops = new window.OperationsPanel(els.opsList, state);
  ops.render();

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

  // ----- file strip + operations panel -----
  strip.onSelect = async (file) => {
    if (file.kind === "base") {
      state.setActive(file);
      return;
    }
    // Output/input files: view side-by-side and target for further operations.
    await state.addCompare(file);
    state.setActive(file);
    setModeButtons(RenderMode.Split);
    state.setRenderMode(RenderMode.Split);
    updateCompareInfo();
  };

  strip.onDelete = async (file) => {
    await window.api.deleteFile(file.id).catch(() => {});
    state.removeFile(file.id);
    updateCompareInfo();
    if (!state.compares.some(Boolean)) {
      setModeButtons(RenderMode.Single);
      state.setRenderMode(RenderMode.Single);
    }
  };

  ops.onStrengthChange = async (fileId, opIndex, strength) => {
    try {
      const info = await window.api.setStrength(fileId, opIndex, strength);
      await state.updateFile(info);
      updateCompareInfo();
    } catch (e) {
      els.compareInfo.textContent = `Strength failed: ${e.message || e}`;
    }
  };

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
  // Track in-flight jobs and resolve each one when its runComplete/runError
  // arrives, so multiple selected models chain onto the same output file
  // (matching the Qt behavior of re-running on the current compare file).
  const activeJobs = new Set();
  const jobResolvers = new Map();
  let autoCompareFirst = false;

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

  function runOneModel(targetId, modelKey, params) {
    return new Promise((resolve, reject) => {
      window.api
        .runModel({
          fileId: targetId,
          modelKey,
          operation: params.operation,
          tileSize: params.tileSize,
          tilePadding: params.tilePadding,
          maintainScale: params.maintainScale,
          device: params.device === "cpu" ? null : params.device,
        })
        .then(({ jobId }) => {
          activeJobs.add(jobId);
          jobResolvers.set(jobId, { resolve, reject });
        })
        .catch(reject);
    });
  }

  async function runOperation(operation) {
    if (!state.base) return;
    const params = await window.openModelDialog(operation);
    if (!params || !params.models.length) return;

    autoCompareFirst = true;
    // Chain onto the active file; running on the base creates a fresh output.
    let targetId = state.active ? state.active.id : "base";
    showProgress(`${operation} queued…`, true);

    for (const modelKey of params.models) {
      try {
        const file = await runOneModel(targetId, modelKey, params);
        targetId = file.id; // subsequent models chain onto the produced output
      } catch (e) {
        els.compareInfo.textContent = `Run failed: ${e.message || e}`;
        break;
      }
    }
    if (activeJobs.size === 0) hideProgress();
  }

  els.sharpen.addEventListener("click", () => runOperation("sharpen"));
  els.denoise.addEventListener("click", () => runOperation("denoise"));
  els.upscale.addEventListener("click", () => runOperation("upscale"));
  els.cancel.addEventListener("click", () => window.api.interrupt().catch(() => {}));

  window.api.on("progress", (p) => {
    if (!activeJobs.has(p.jobId)) return;
    if (p.statusMessage) {
      showProgress(p.statusMessage, true);
    } else if (p.total) {
      els.progress.classList.remove("hidden");
      els.progressBar.classList.remove("indeterminate");
      els.progressLabel.textContent = `Processing ${p.count}/${p.total}`;
      els.progressBar.style.width = `${Math.round((p.count / p.total) * 100)}%`;
    }
  });

  // A fresh output file was created for a base run: show it in the strip and
  // make it the active target so chained models append to it.
  window.api.on("fileAppended", (info) => {
    state.setActive(info);
  });

  window.api.on("runComplete", async (payload) => {
    activeJobs.delete(payload.jobId);
    const canonical = await state.updateFile(payload.file);
    await state.addCompare(canonical);
    state.setActive(canonical);
    if (autoCompareFirst) {
      autoCompareFirst = false;
      setModeButtons(RenderMode.Split);
      state.setRenderMode(RenderMode.Split);
    }
    updateCompareInfo();

    const r = jobResolvers.get(payload.jobId);
    if (r) {
      jobResolvers.delete(payload.jobId);
      r.resolve(canonical);
    }
    if (activeJobs.size === 0) hideProgress();
  });

  window.api.on("runError", (payload) => {
    activeJobs.delete(payload.jobId);
    els.compareInfo.textContent = `Run failed: ${payload.message}`;
    const r = jobResolvers.get(payload.jobId);
    if (r) {
      jobResolvers.delete(payload.jobId);
      r.reject(new Error(payload.message));
    }
    if (activeJobs.size === 0) hideProgress();
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
