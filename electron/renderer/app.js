// Placeholder renderer wiring: open an image, show its preview, live GPU stats.
// Proves the transport + preview pipeline end-to-end before porting the viewer.

(function () {
  const btnOpen = document.getElementById("btnOpen");
  const filenameEl = document.getElementById("filename");
  const gpuEl = document.getElementById("gpu");
  const previewEl = document.getElementById("preview");
  const placeholderEl = document.getElementById("placeholder");

  function renderGpu(stats) {
    if (!stats || !stats.present) {
      gpuEl.textContent = "GPU: none";
      return;
    }
    const parts = [];
    if (stats.utilization != null) {
      parts.push(`${Math.round(stats.utilization * 100)}%`);
    }
    if (stats.memoryTotalGb != null && stats.memoryAvailableGb != null) {
      const used = stats.memoryTotalGb - stats.memoryAvailableGb;
      parts.push(`${used.toFixed(1)}/${stats.memoryTotalGb.toFixed(1)}GB`);
    }
    gpuEl.textContent = `GPU: ${parts.join("  ") || stats.preferredDevice}`;
  }

  async function showPreview(fileId) {
    const preview = await window.api.getPreview(fileId);
    previewEl.src = window.api.assetUrl(preview.url);
    previewEl.style.display = "block";
    placeholderEl.style.display = "none";
  }

  btnOpen.addEventListener("click", async () => {
    const path = await window.native.openImage();
    if (!path) return;
    const info = await window.api.setBaseFile(path);
    filenameEl.textContent = info.basename || path;
    filenameEl.classList.remove("muted");
    await showPreview("base");
  });

  // Live GPU stats via WebSocket (replaces the Qt QTimer poll).
  window.api.on("gpuStats", renderGpu);
  window.api.connectWebSocket();

  // Initial one-shot fetch so the footer isn't blank before the first push.
  window.api.getGpu().then(renderGpu).catch(() => {});
})();
