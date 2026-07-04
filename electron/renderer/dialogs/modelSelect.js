// Model-select modal — ports DialogModel (installed models filtered by operation,
// tile size/padding, device, maintain-scale, and optional mask restriction).

(function () {
  const TILE_SIZES = [64, 128, 256, 512, 1024];
  const TILE_PADDINGS = [0, 8, 16, 32];

  function optionEls(values, selected) {
    return values
      .map(
        (v) =>
          `<option value="${v}"${v === selected ? " selected" : ""}>${v}</option>`
      )
      .join("");
  }

  // Show the modal. Returns a Promise resolving to the chosen params, or null if
  // cancelled.
  async function openModelDialog(operation) {
    const [models, devices] = await Promise.all([
      window.api.getModels(true),
      window.api.getDevices(),
    ]);

    // Filter installed models to the requested operation.
    const modelKeys = Object.keys(models).filter((key) => {
      const ops = models[key].operation;
      return Array.isArray(ops) && ops.length > 0 && ops[0] === operation;
    });

    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";

      const deviceOpts = devices
        .map(
          (d, i) =>
            `<option value="${d.id}"${
              i === (devices.length > 1 ? 1 : 0) ? " selected" : ""
            }>${d.name}</option>`
        )
        .join("");

      const modelOpts = modelKeys.length
        ? modelKeys.map((k) => `<option value="${k}">${k}</option>`).join("")
        : "";

      // Masks detected on the base file (Phase 5): allow restricting the run.
      const masks = (window.selectionState && window.selectionState.masks) || [];
      const maskOpts = masks
        .map(
          (m) =>
            `<option value="${m.index}">${m.uniqueLabel}</option>`
        )
        .join("");

      overlay.innerHTML = `
        <div class="modal">
          <h2>${operation[0].toUpperCase() + operation.slice(1)}</h2>
          ${
            modelKeys.length
              ? `<label>Models (multi-select)</label>
                 <select id="ms-models" multiple size="6">${modelOpts}</select>`
              : `<p class="muted">No installed ${operation} models. Use the Model Manager to install one.</p>`
          }
          <div class="modal-row">
            <label>Tile size
              <select id="ms-tile">${optionEls(TILE_SIZES, 512)}</select>
            </label>
            <label>Tile padding
              <select id="ms-pad">${optionEls(TILE_PADDINGS, 32)}</select>
            </label>
          </div>
          <div class="modal-row">
            <label>Device
              <select id="ms-device">${deviceOpts}</select>
            </label>
            <label class="checkbox">
              <input type="checkbox" id="ms-scale" ${
                operation === "upscale" ? "" : "checked"
              } />
              Maintain scale
            </label>
          </div>
          ${
            masks.length
              ? `<label>Restrict to masks (optional)
                   <select id="ms-masks" multiple size="4">${maskOpts}</select>
                 </label>
                 <label class="checkbox">
                   <input type="checkbox" id="ms-mask-invert" />
                   Apply outside selected masks
                 </label>`
              : ""
          }
          <div class="modal-actions">
            <button id="ms-cancel">Cancel</button>
            <button id="ms-ok" class="primary"${
              modelKeys.length ? "" : " disabled"
            }>Run</button>
          </div>
        </div>`;

      document.body.appendChild(overlay);

      const close = (result) => {
        document.body.removeChild(overlay);
        resolve(result);
      };

      overlay.querySelector("#ms-cancel").addEventListener("click", () => close(null));
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close(null);
      });

      const okBtn = overlay.querySelector("#ms-ok");
      if (okBtn && modelKeys.length) {
        okBtn.addEventListener("click", () => {
          const selected = Array.from(
            overlay.querySelector("#ms-models").selectedOptions
          ).map((o) => o.value);
          if (selected.length === 0) return;
          const maskSel = overlay.querySelector("#ms-masks");
          const invert = overlay.querySelector("#ms-mask-invert");
          const masks = maskSel
            ? Array.from(maskSel.selectedOptions).map((o) => ({
                index: parseInt(o.value, 10),
                inverted: !!(invert && invert.checked),
              }))
            : [];
          close({
            models: selected,
            operation,
            tileSize: parseInt(overlay.querySelector("#ms-tile").value, 10),
            tilePadding: parseInt(overlay.querySelector("#ms-pad").value, 10),
            device: overlay.querySelector("#ms-device").value,
            maintainScale: overlay.querySelector("#ms-scale").checked,
            masks,
          });
        });
      }
    });
  }

  window.openModelDialog = openModelDialog;
})();
