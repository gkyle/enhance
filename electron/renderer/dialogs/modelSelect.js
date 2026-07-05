// Model-select modal — ports DialogModel (installed models filtered by operation,
// tile size/padding, device, maintain-scale, and optional mask restriction).

(function () {
  const TILE_SIZES = [64, 128, 256, 512, 1024];
  const TILE_PADDINGS = [0, 8, 16, 32];
  const STRENGTH_PREFIX = "enhance.modelStrength.";

  function optionEls(values, selected) {
    return values
      .map(
        (v) =>
          `<option value="${v}"${v === selected ? " selected" : ""}>${v}</option>`
      )
      .join("");
  }

  function rememberedStrength(modelKey) {
    const raw = localStorage.getItem(`${STRENGTH_PREFIX}${modelKey}`);
    const last = raw == null ? 1 : parseFloat(raw);
    if (!Number.isFinite(last)) return 80;
    return Math.max(0, Math.min(100, Math.round(last * 80)));
  }

  function storeStrength(modelKey, pct) {
    localStorage.setItem(`${STRENGTH_PREFIX}${modelKey}`, String(pct / 100));
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
        ? modelKeys
            .map((k, i) => `<option value="${k}"${i === 0 ? " selected" : ""}>${k}</option>`)
            .join("")
        : "";
      const initialStrength = modelKeys.length ? rememberedStrength(modelKeys[0]) : 80;

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
          <label>
            <span class="range-head"><span>Strength</span><span id="ms-strength-label">${initialStrength}%</span></span>
            <input type="range" id="ms-strength" min="0" max="100" value="${initialStrength}" />
          </label>
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

      const modelSelect = overlay.querySelector("#ms-models");
      const strength = overlay.querySelector("#ms-strength");
      const strengthLabel = overlay.querySelector("#ms-strength-label");
      if (strength) {
        strength.addEventListener("input", () => {
          strengthLabel.textContent = `${strength.value}%`;
        });
      }
      if (modelSelect && strength) {
        modelSelect.addEventListener("change", () => {
          const first = modelSelect.selectedOptions[0];
          if (!first) return;
          strength.value = String(rememberedStrength(first.value));
          strengthLabel.textContent = `${strength.value}%`;
        });
      }

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
          const strengthPct = parseInt(overlay.querySelector("#ms-strength").value, 10);
          selected.forEach((modelKey) => storeStrength(modelKey, strengthPct));
          close({
            models: selected,
            operation,
            tileSize: parseInt(overlay.querySelector("#ms-tile").value, 10),
            tilePadding: parseInt(overlay.querySelector("#ms-pad").value, 10),
            device: overlay.querySelector("#ms-device").value,
            maintainScale: overlay.querySelector("#ms-scale").checked,
            masks,
            strength: strengthPct / 100,
          });
        });
      }
    });
  }

  window.openModelDialog = openModelDialog;
})();
