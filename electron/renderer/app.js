// Renderer wiring: open base/compare images, switch render modes, zoom menu,
// and live GPU stats. Drives the canvas Viewer via selectionState.

(function () {
  const RenderMode = window.RenderMode;
  const state = window.selectionState;

  const els = {
    open: document.getElementById("btnOpen"),
    clear: document.getElementById("btnClear"),
    sharpen: document.getElementById("btnSharpen"),
    denoise: document.getElementById("btnDenoise"),
    upscale: document.getElementById("btnUpscale"),
    automask: document.getElementById("btnAutomask"),
    modelManager: document.getElementById("btnModelManager"),
    taskQueue: document.getElementById("btnTaskQueue"),
    single: document.getElementById("btnSingle"),
    split: document.getElementById("btnSplit"),
    grid: document.getElementById("btnGrid"),
    zoom: document.getElementById("btnZoom"),
    zoomLabel: document.getElementById("zoomLabel"),
    zoomMenu: document.getElementById("zoomMenu"),
    filename: document.getElementById("filename"),
    gpu: document.getElementById("gpu"),
    gpuUtil: document.getElementById("gpuUtil"),
    gpuUtilFill: document.getElementById("gpuUtilFill"),
    gpuUtilLabel: document.getElementById("gpuUtilLabel"),
    gpuMem: document.getElementById("gpuMem"),
    gpuMemFill: document.getElementById("gpuMemFill"),
    gpuMemLabel: document.getElementById("gpuMemLabel"),
    placeholder: document.getElementById("placeholder"),
    compareInfo: document.getElementById("compareInfo"),
    canvas: document.getElementById("canvas"),
    opsList: document.getElementById("opsList"),
    compareActions: document.getElementById("compareActions"),
    saveCompare: document.getElementById("btnSaveCompare"),
    deleteCompare: document.getElementById("btnDeleteCompare"),
    maskHeader: document.getElementById("maskHeader"),
    maskList: document.getElementById("maskList"),
    maskToggleAll: document.getElementById("btnMaskToggleAll"),
    filestrip: document.getElementById("filestripInner"),
    progress: document.getElementById("progress"),
    progressLabel: document.getElementById("progressLabel"),
    progressBar: document.getElementById("progressBar"),
    cancel: document.getElementById("btnCancel"),
  };

  const viewer = new window.Viewer(els.canvas, state);
  viewer.onZoomChange = (z) => {
    els.zoomLabel.textContent = `${Math.round(z * 100)}%`;
  };

  const strip = new window.FileStrip(els.filestrip, state);
  const ops = new window.OperationsPanel(els.opsList, state);
  ops.render();

  function renderCompareActions() {
    const file = state.active;
    const show = file && file.kind === "output" && !file.saved;
    els.compareActions.classList.toggle("hidden", !show);
  }
  state.onFilesChange(renderCompareActions);

  // ----- mask visibility panel (ports MaskVisibilityList; default all hidden) -----
  function renderMaskPanel() {
    const masks = state.masks || [];
    els.maskHeader.classList.toggle("hidden", masks.length === 0);
    if (masks.length === 0) {
      els.maskList.innerHTML = "";
      return;
    }
    els.maskList.innerHTML = "";
    for (const m of masks) {
      const row = document.createElement("label");
      row.className = "mask-row";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = state.visibleMaskIndices.has(m.index);
      cb.addEventListener("change", () => {
        state.setMaskVisible(m.index, cb.checked);
        updateToggleAllLabel();
      });
      const swatch = document.createElement("span");
      swatch.className = "mask-swatch";
      swatch.style.background = maskColor(m.index);
      const label = document.createElement("span");
      label.className = "mask-row-label";
      label.textContent = `${m.uniqueLabel}  (${Math.round((m.score || 0) * 100)}%)`;
      row.appendChild(cb);
      row.appendChild(swatch);
      row.appendChild(label);
      els.maskList.appendChild(row);
    }
    updateToggleAllLabel();
  }

  function updateToggleAllLabel() {
    const masks = state.masks || [];
    const allOn = masks.length > 0 && masks.every((m) => state.visibleMaskIndices.has(m.index));
    els.maskToggleAll.textContent = allOn ? "Hide all" : "Show all";
  }

  function maskColor(index) {
    const colors = [
      "rgb(66,135,245)",
      "rgb(80,200,120)",
      "rgb(231,76,60)",
      "rgb(52,152,219)",
      "rgb(155,89,182)",
      "rgb(212,188,60)",
    ];
    return colors[index % colors.length];
  }

  els.maskToggleAll.addEventListener("click", () => {
    const masks = state.masks || [];
    const allOn = masks.length > 0 && masks.every((m) => state.visibleMaskIndices.has(m.index));
    state.setAllMasksVisible(!allOn);
    renderMaskPanel();
  });

  state.onMasksChange(renderMaskPanel);

  function setModeButtons(mode) {
    [els.single, els.split, els.grid].forEach((b) => b.classList.remove("active"));
    if (mode === RenderMode.Single) els.single.classList.add("active");
    if (mode === RenderMode.Split) els.split.classList.add("active");
    if (mode === RenderMode.Grid) els.grid.classList.add("active");
  }

  function enableViewerControls() {
    [els.sharpen, els.denoise, els.upscale, els.automask, els.single, els.split, els.grid, els.zoom, els.clear].forEach(
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

  async function deleteOutputFile(file) {
    await window.api.deleteFile(file.id).catch(() => {});
    state.removeFile(file.id);
    updateCompareInfo();
    renderCompareActions();
    if (!state.compares.some(Boolean)) {
      setModeButtons(RenderMode.Single);
      state.setRenderMode(RenderMode.Single);
    }
  }

  async function saveOutputFile(file) {
    const target = await window.native.saveImage(file.basename);
    if (!target) return;
    try {
      const info = await window.api.saveFile(file.id, target);
      await state.updateFile(info);
    } catch (e) {
      els.compareInfo.textContent = `Save failed: ${e.message || e}`;
    }
    renderCompareActions();
  }

  strip.onDelete = deleteOutputFile;
  strip.onSave = saveOutputFile;

  els.deleteCompare.addEventListener("click", () => {
    if (state.active && state.active.kind === "output") deleteOutputFile(state.active);
  });
  els.saveCompare.addEventListener("click", () => {
    if (state.active && state.active.kind === "output") saveOutputFile(state.active);
  });

  ops.onStrengthChange = async (fileId, opIndex, strength) => {
    try {
      const info = await window.api.setStrength(fileId, opIndex, strength);
      await state.updateFile(info);
      updateCompareInfo();
    } catch (e) {
      els.compareInfo.textContent = `Strength failed: ${e.message || e}`;
    }
  };

  ops.onMasksChange = async (fileId, opIndex, masks) => {
    try {
      showProgress("Updating Masks", true);
      const info = await window.api.setOperationMasks(fileId, opIndex, masks);
      const canonical = await state.updateFile(info);
      state.setActive(canonical);
      updateCompareInfo();
    } catch (e) {
      els.compareInfo.textContent = `Mask update failed: ${e.message || e}`;
    } finally {
      hideProgress();
    }
  };

  // ----- open / add -----
  async function loadBase(path) {
    const info = await window.api.setBaseFile(path);
    els.filename.textContent = info.basename || path;
    els.filename.classList.remove("muted");
    await state.setBase(info);
    await state.setMasks([]);
    enableViewerControls();
    updateCompareInfo();
    return info;
  }

  els.open.addEventListener("click", async () => {
    const path = await window.native.openImage();
    if (!path) return;
    await loadBase(path);
  });

  // ----- clear -----
  els.clear.addEventListener("click", () => {
    state.clear();
    els.filename.textContent = "No image loaded";
    els.filename.classList.add("muted");
    els.compareInfo.textContent = "";
    setModeButtons(RenderMode.Single);
    [els.sharpen, els.denoise, els.upscale, els.automask, els.single, els.split, els.grid, els.zoom, els.clear].forEach(
      (b) => (b.disabled = true)
    );
    els.placeholder.style.display = "";
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
  const autoMaskJobs = new Set();
  let autoCompareFirst = false;
  // Operation description shown on the progress label for the whole job
  // (ports the Qt `desc` on ProgressBarUpdater, e.g. "Sharpen").
  let currentOpLabel = "";

  function setProgressLabel(detail) {
    els.progressLabel.textContent = detail
      ? `${currentOpLabel} — ${detail}`
      : currentOpLabel;
  }

  function showProgress(opLabel, indeterminate) {
    currentOpLabel = opLabel;
    els.cancel.classList.remove("hidden");
    setProgressLabel("");
    els.progressBar.classList.toggle("indeterminate", !!indeterminate);
    if (indeterminate) els.progressBar.style.width = "";
    else els.progressBar.style.width = "0%";
  }

  function hideProgress() {
    // The bar stays visible (idle at 0%); only the job UI is reset.
    currentOpLabel = "";
    els.cancel.classList.add("hidden");
    els.progressLabel.textContent = "";
    els.progressBar.classList.remove("indeterminate");
    els.progressBar.style.width = "0%";
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
          masks: params.masks && params.masks.length ? params.masks : null,
          strength: params.strength,
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
    const opLabel = operation.charAt(0).toUpperCase() + operation.slice(1);
    showProgress(opLabel, true);

    for (const modelKey of params.models) {
      try {
        const file = await runOneModel(targetId, modelKey, params);
        targetId = file.id; // subsequent models chain onto the produced output
      } catch (e) {
        els.compareInfo.textContent = `Run failed: ${e.message || e}`;
        break;
      }
    }
    state.setAllMasksVisible(false);
    if (activeJobs.size === 0) hideProgress();
  }

  els.sharpen.addEventListener("click", () => runOperation("sharpen"));
  els.denoise.addEventListener("click", () => runOperation("denoise"));
  els.upscale.addEventListener("click", () => runOperation("upscale"));
  els.cancel.addEventListener("click", () => window.api.interrupt().catch(() => {}));

  els.modelManager.addEventListener("click", () => window.openModelManager());
  els.taskQueue.addEventListener("click", () => window.openTaskQueue());

  // Auto-detect masks on the base image (Florence + SAM); results push back over
  // the "masksUpdated" websocket event and populate the mask visibility panel.
  els.automask.addEventListener("click", async () => {
    if (!state.base) return;
    els.automask.disabled = true;
    showProgress("Generating Masks", true);
    try {
      const { jobId } = await window.api.autoMask("base");
      autoMaskJobs.add(jobId);
    } catch (e) {
      els.compareInfo.textContent = `Auto mask failed: ${e.message || e}`;
      hideProgress();
      els.automask.disabled = false;
    }
  });

  window.api.on("progress", (p) => {
    if (!activeJobs.has(p.jobId) && !autoMaskJobs.has(p.jobId)) return;
    if (p.statusMessage) {
      els.cancel.classList.remove("hidden");
      els.progressBar.classList.add("indeterminate");
      els.progressBar.style.width = "";
      setProgressLabel(p.statusMessage);
    } else if (p.total) {
      els.cancel.classList.remove("hidden");
      els.progressBar.classList.remove("indeterminate");
      setProgressLabel(`${p.count}/${p.total}`);
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
    state.setAllMasksVisible(false);
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

  // Auto-mask completion: ingest detected masks (default all hidden) and clear
  // the detection progress. Payload carries { jobId, fileId, masks }.
  window.api.on("masksUpdated", async (payload) => {
    if (payload.jobId != null) autoMaskJobs.delete(payload.jobId);
    els.automask.disabled = false;
    try {
      const masks = payload.masks || (await window.api.getMasks(payload.fileId || "base"));
      await state.setMasks(masks, { visible: true });
    } catch (e) {
      els.compareInfo.textContent = `Load masks failed: ${e.message || e}`;
    }
    if (activeJobs.size === 0 && autoMaskJobs.size === 0) hideProgress();
  });

  // ----- GPU stats -----
  function renderGpu(stats) {
    if (!stats || !stats.present) {
      els.gpuUtil.style.display = "";
      els.gpuUtilFill.style.width = "0%";
      els.gpuUtilLabel.textContent = "GPU: none";
      els.gpuMem.style.display = "none";
      return;
    }

    if (stats.utilization != null) {
      const pct = Math.round(stats.utilization * 100);
      els.gpuUtil.style.display = "";
      els.gpuUtilFill.style.width = `${pct}%`;
      els.gpuUtilLabel.textContent = `GPU: ${pct}%`;
    } else {
      els.gpuUtil.style.display = "none";
    }

    if (stats.memoryTotalGb != null && stats.memoryAvailableGb != null) {
      const used = stats.memoryTotalGb - stats.memoryAvailableGb;
      const pct = Math.round((used / stats.memoryTotalGb) * 100);
      els.gpuMem.style.display = "";
      els.gpuMemFill.style.width = `${pct}%`;
      els.gpuMemLabel.textContent = `Mem: ${pct}%  ${used.toFixed(1)}/${stats.memoryTotalGb.toFixed(1)}GB`;
    } else {
      els.gpuMem.style.display = "none";
    }
  }

  window.api.on("gpuStats", renderGpu);
  window.api.connectWebSocket();
  window.api.getGpu().then(renderGpu).catch(() => {});

  // ----- startup base image (passed via ?startup= from main.js) -----
  const startupPath = new URLSearchParams(window.location.search).get("startup");
  if (startupPath) {
    loadBase(startupPath).catch((e) => {
      els.compareInfo.textContent = `Could not load ${startupPath}: ${e.message || e}`;
    });
  }
})();
