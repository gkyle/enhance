// Task queue modal — ports DialogTaskQueue (WorkerHistory). Lists every job the
// backend has scheduled with its status, device, and latency. Live-updates from
// the `tasksUpdated` WebSocket push while open.

(function () {
  function fmtTime(epoch) {
    if (!epoch) return "";
    const d = new Date(epoch * 1000);
    return d.toLocaleTimeString();
  }

  function fmtLatency(sec) {
    if (sec == null) return "";
    return `${sec.toFixed(1)}s`;
  }

  async function openTaskQueue() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal modal-wide">
        <h2>Task Queue</h2>
        <div class="mm-table-wrap">
          <table class="mm-table">
            <thead>
              <tr><th>#</th><th>Task</th><th>Device</th><th>Status</th><th>Scheduled</th><th>Latency</th></tr>
            </thead>
            <tbody id="tq-body"></tbody>
          </table>
          <div id="tq-empty" class="muted mm-empty hidden">No tasks yet.</div>
        </div>
        <div class="modal-actions">
          <button id="tq-close">Close</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const body = overlay.querySelector("#tq-body");
    const empty = overlay.querySelector("#tq-empty");

    function render(tasks) {
      empty.classList.toggle("hidden", tasks.length > 0);
      body.innerHTML = "";
      // Newest first.
      tasks
        .slice()
        .reverse()
        .forEach((t) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${t.id}</td>
            <td title="${t.label}">${t.label}</td>
            <td>${t.device || ""}</td>
            <td><span class="tq-status tq-${t.status}">${t.status}</span></td>
            <td>${fmtTime(t.scheduleTime)}</td>
            <td>${fmtLatency(t.latency)}</td>`;
          body.appendChild(tr);
        });
    }

    const onUpdate = (tasks) => render(tasks || []);
    window.api.on("tasksUpdated", onUpdate);

    try {
      render(await window.api.getTasks());
    } catch (e) {
      render([]);
    }

    const close = () => {
      window.api.off("tasksUpdated", onUpdate);
      document.body.removeChild(overlay);
    };

    overlay.querySelector("#tq-close").addEventListener("click", close);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });
  }

  window.openTaskQueue = openTaskQueue;
})();
