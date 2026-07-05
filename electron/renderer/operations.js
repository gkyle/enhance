// Operations panel: shows the applied-operation chain for the active output file
// (ported from Qt OperationWidget). Each operation renders its type, model, and a
// debounced strength slider that re-blends the chain via /operation/strength
// without re-running the model. Mask changes re-run the selected operation and
// any later operations because masks affect model inference.

(function () {
  const STRENGTH_DEBOUNCE_MS = 400; // matches the Qt 500ms strength timer

  class OperationsPanel {
    constructor(container, state) {
      this.container = container;
      this.state = state;
      this.onStrengthChange = null; // (fileId, opIndex, strength) => void
      this.onMasksChange = null; // (fileId, opIndex, masks) => void
      this._signature = null;
      this._timers = new Map();
      state.onFilesChange(() => this.render());
      state.onMasksChange(() => this.render());
    }

    _sig(file) {
      if (!file || file.kind !== "output") return `empty:${file ? file.id : ""}`;
      const ops = (file.operations || [])
        .map(
          (o) =>
            `${o.operationType}|${o.model}|${o.supportsStrength}|${this._maskKey(o)}`
        )
        .join(",");
      return `${file.id}#${ops}`;
    }

    _maskKey(op) {
      return (op.masks || [])
        .map((m) => `${m.index}:${m.inverted ? "out" : "in"}`)
        .join(",");
    }

    render() {
      const file = this.state.active;
      const sig = this._sig(file);
      if (sig === this._signature) return; // avoid rebuild during slider drags
      this._signature = sig;

      this.container.innerHTML = "";

      if (!file || file.kind !== "output" || !(file.operations || []).length) {
        const hint = document.createElement("div");
        hint.className = "ops-hint muted";
        hint.textContent = file
          ? "No operations yet. Run Sharpen, Denoise, or Upscale."
          : "Select a file to view its operations.";
        this.container.appendChild(hint);
        return;
      }

      file.operations.forEach((op) => this._renderOp(file, op));
    }

    _renderOp(file, op) {
      const card = document.createElement("div");
      card.className = "op-card";

      const title = document.createElement("div");
      title.className = "op-title";
      title.textContent = op.operationType || "operation";
      card.appendChild(title);

      if (op.model) {
        const model = document.createElement("div");
        model.className = "op-model";
        model.textContent = middleEllipsis(op.model, 34);
        model.title = op.model;
        card.appendChild(model);
      }

      if (op.scale != null && op.scale < 1.0) {
        const scale = document.createElement("div");
        scale.className = "op-scale";
        scale.textContent = `Downscale ${Math.round(1 / op.scale)}X`;
        card.appendChild(scale);
      }

      if (op.supportsStrength) {
        const row = document.createElement("div");
        row.className = "op-strength";

        const head = document.createElement("div");
        head.className = "op-strength-head";
        const lab = document.createElement("span");
        lab.textContent = "Strength";
        const val = document.createElement("span");
        const pct = Math.round((op.strength != null ? op.strength : 1) * 100);
        val.textContent = `${pct}%`;
        head.appendChild(lab);
        head.appendChild(val);
        row.appendChild(head);

        const slider = document.createElement("input");
        slider.type = "range";
        slider.min = "0";
        slider.max = "100";
        slider.value = String(pct);
        slider.addEventListener("input", () => {
          val.textContent = `${slider.value}%`;
          const key = `${file.id}:${op.index}`;
          if (this._timers.has(key)) clearTimeout(this._timers.get(key));
          this._timers.set(
            key,
            setTimeout(() => {
              this._timers.delete(key);
              if (this.onStrengthChange) {
                this.onStrengthChange(file.id, op.index, Number(slider.value) / 100);
              }
            }, STRENGTH_DEBOUNCE_MS)
          );
        });
        row.appendChild(slider);
        card.appendChild(row);
      }

      const maskRow = document.createElement("div");
      maskRow.className = "op-mask-row";

      const masks = document.createElement("div");
      masks.className = "op-masks";
      masks.textContent = maskSummary(op, this.state.masks);
      maskRow.appendChild(masks);

      const edit = document.createElement("button");
      edit.className = "op-mask-edit";
      edit.textContent = "Edit";
      edit.disabled = !(this.state.masks || []).length;
      edit.title = edit.disabled ? "No masks available" : "Edit masks";
      edit.addEventListener("click", () => this._openMaskDialog(file, op));
      maskRow.appendChild(edit);
      card.appendChild(maskRow);

      this.container.appendChild(card);
    }

    _openMaskDialog(file, op) {
      const available = this.state.masks || [];
      if (!available.length) return;

      const selected = new Map(
        (op.masks || []).map((m) => [m.index, { inverted: !!m.inverted }])
      );

      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal">
          <h2>Edit Masks</h2>
          <div class="mask-edit-list"></div>
          <div class="modal-actions">
            <button id="om-cancel">Cancel</button>
            <button id="om-ok" class="primary">Apply</button>
          </div>
        </div>`;

      const list = overlay.querySelector(".mask-edit-list");
      for (const mask of available) {
        const row = document.createElement("label");
        row.className = "mask-edit-row";

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = selected.has(mask.index);
        cb.dataset.index = String(mask.index);

        const swatch = document.createElement("span");
        swatch.className = "mask-swatch";
        swatch.style.background = maskColor(mask.index);

        const name = document.createElement("span");
        name.className = "mask-edit-name";
        name.textContent = mask.uniqueLabel;

        const mode = document.createElement("select");
        mode.dataset.index = String(mask.index);
        mode.innerHTML = `
          <option value="inside">Inside</option>
          <option value="outside">Outside</option>`;
        mode.value = selected.get(mask.index)?.inverted ? "outside" : "inside";

        row.appendChild(cb);
        row.appendChild(swatch);
        row.appendChild(name);
        row.appendChild(mode);
        list.appendChild(row);
      }

      const close = () => document.body.removeChild(overlay);
      overlay.querySelector("#om-cancel").addEventListener("click", close);
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close();
      });
      overlay.querySelector("#om-ok").addEventListener("click", () => {
        const masks = Array.from(overlay.querySelectorAll(".mask-edit-row"))
          .map((row) => {
            const cb = row.querySelector("input[type='checkbox']");
            const mode = row.querySelector("select");
            return {
              checked: cb.checked,
              index: parseInt(cb.dataset.index, 10),
              inverted: mode.value === "outside",
            };
          })
          .filter((m) => m.checked)
          .map(({ index, inverted }) => ({ index, inverted }));
        close();
        if (this.onMasksChange) this.onMasksChange(file.id, op.index, masks);
      });

      document.body.appendChild(overlay);
    }
  }

  function middleEllipsis(text, max) {
    if (!text || text.length <= max) return text || "";
    const keep = Math.max(4, max - 3);
    const head = Math.ceil(keep / 2);
    const tail = Math.floor(keep / 2);
    return `${text.slice(0, head)}...${text.slice(text.length - tail)}`;
  }

  function maskSummary(op, available) {
    const selected = op.masks || [];
    if (selected.length) {
      const byIndex = new Map((available || []).map((m) => [m.index, m]));
      const labels = selected.map((sel) => {
        const label = byIndex.get(sel.index)?.uniqueLabel || `Mask ${sel.index + 1}`;
        return `${label} (${sel.inverted ? "outside" : "inside"})`;
      });
      return `Masks: ${labels.join(", ")}`;
    }
    if (op.maskLabels && op.maskLabels.length) {
      return `Masks: ${op.maskLabels.join(", ")}`;
    }
    return "Masks: None";
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

  window.OperationsPanel = OperationsPanel;
})();
