// Model manager modal — ports DialogModelManager: a filterable table of all known
// models (operation/subject filters), install buttons for uninstalled models, and
// a refresh action that re-fetches the remote model list. Installs and refresh hit
// the network, so the modal shows a busy state while they run.

(function () {
  function firstOf(list) {
    return Array.isArray(list) && list.length ? list[0] : null;
  }

  async function openModelManager() {
    let models = await window.api.getModels(false);

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal modal-wide">
        <h2>Model Manager</h2>
        <div class="modal-row">
          <label>Filter operation
            <select id="mm-op"></select>
          </label>
          <label>Filter subject
            <select id="mm-subject"></select>
          </label>
          <button id="mm-refresh" class="mm-refresh">Refresh Model List</button>
        </div>
        <div class="mm-table-wrap">
          <table class="mm-table">
            <thead>
              <tr><th>Operation</th><th>Name</th><th>Subject</th><th></th><th>Author</th></tr>
            </thead>
            <tbody id="mm-body"></tbody>
          </table>
          <div id="mm-empty" class="muted mm-empty hidden">
            Local model list is empty. Click "Refresh Model List".
          </div>
        </div>
        <div class="modal-actions">
          <button id="mm-close">Close</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const opSel = overlay.querySelector("#mm-op");
    const subjectSel = overlay.querySelector("#mm-subject");
    const body = overlay.querySelector("#mm-body");
    const empty = overlay.querySelector("#mm-empty");
    const refreshBtn = overlay.querySelector("#mm-refresh");

    let selectedOp = "All";
    let selectedSubject = "All";

    function populateFilters() {
      const ops = new Set();
      const subjects = new Set();
      Object.values(models).forEach((m) => {
        const op = firstOf(m.operation);
        if (op) ops.add(op);
        const s = firstOf(m.subject);
        if (s) subjects.add(s);
      });
      opSel.innerHTML =
        `<option>All</option>` +
        [...ops].sort().map((o) => `<option>${o}</option>`).join("");
      subjectSel.innerHTML =
        `<option>All</option>` +
        [...subjects].sort().map((s) => `<option>${s}</option>`).join("");
      opSel.value = selectedOp;
      subjectSel.value = selectedSubject;
    }

    function draw() {
      const keys = Object.keys(models);
      empty.classList.toggle("hidden", keys.length > 0);
      body.innerHTML = "";
      for (const key of keys) {
        const m = models[key];
        const op = firstOf(m.operation);
        const subject = firstOf(m.subject);
        if (selectedOp !== "All" && op !== selectedOp) continue;
        if (selectedSubject !== "All" && subject !== selectedSubject) continue;

        const tr = document.createElement("tr");
        const opCell = (m.operation || []).join(", ");
        const subjCell = (m.subject || []).join(", ");
        tr.innerHTML = `
          <td>${opCell}</td>
          <td title="${key}">${m.name || key}</td>
          <td>${subjCell}</td>
          <td class="mm-install-cell"></td>
          <td>${m.author || ""}</td>`;
        const cell = tr.querySelector(".mm-install-cell");
        if (m.installed) {
          cell.innerHTML = `<span class="mm-installed">Installed</span>`;
        } else {
          const btn = document.createElement("button");
          btn.textContent = "Install";
          btn.addEventListener("click", async () => {
            btn.disabled = true;
            btn.textContent = "Installing…";
            try {
              models = await window.api.installModel(key);
              draw();
            } catch (e) {
              btn.disabled = false;
              btn.textContent = "Retry";
            }
          });
          cell.appendChild(btn);
        }
        body.appendChild(tr);
      }
    }

    opSel.addEventListener("change", () => {
      selectedOp = opSel.value;
      draw();
    });
    subjectSel.addEventListener("change", () => {
      selectedSubject = subjectSel.value;
      draw();
    });
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Refreshing…";
      try {
        models = await window.api.refreshModels();
        selectedOp = "All";
        selectedSubject = "All";
        populateFilters();
        draw();
      } catch (e) {
        // leave existing list
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh Model List";
      }
    });

    const close = () => document.body.removeChild(overlay);
    overlay.querySelector("#mm-close").addEventListener("click", close);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });

    populateFilters();
    draw();
  }

  window.openModelManager = openModelManager;
})();
