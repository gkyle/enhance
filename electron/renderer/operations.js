// Operations panel: shows the applied-operation chain for the active output file
// (ported from Qt OperationWidget). Each operation renders its type, model, and a
// debounced strength slider that re-blends the chain via /operation/strength
// without re-running the model. Mask editing arrives in Phase 5; mask labels are
// shown read-only here.

(function () {
  const STRENGTH_DEBOUNCE_MS = 400; // matches the Qt 500ms strength timer

  class OperationsPanel {
    constructor(container, state) {
      this.container = container;
      this.state = state;
      this.onStrengthChange = null; // (fileId, opIndex, strength) => void
      this._signature = null;
      this._timers = new Map();
      state.onFilesChange(() => this.render());
    }

    _sig(file) {
      if (!file || file.kind !== "output") return `empty:${file ? file.id : ""}`;
      const ops = (file.operations || [])
        .map((o) => `${o.operationType}|${o.model}|${o.supportsStrength}`)
        .join(",");
      return `${file.id}#${ops}`;
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
        model.textContent = op.model;
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

      if (op.maskLabels && op.maskLabels.length) {
        const masks = document.createElement("div");
        masks.className = "op-masks";
        masks.textContent = `Masks: ${op.maskLabels.join(", ")}`;
        card.appendChild(masks);
      }

      this.container.appendChild(card);
    }
  }

  window.OperationsPanel = OperationsPanel;
})();
