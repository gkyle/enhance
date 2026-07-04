// Minimal REST + WebSocket client for the backend service.
// Ported incrementally into the full `api.js` event bus later.

(function () {
  const params = new URLSearchParams(window.location.search);
  const backend = params.get("backend") || "http://127.0.0.1:8420";

  const listeners = {};

  function on(type, fn) {
    (listeners[type] = listeners[type] || []).push(fn);
  }

  function emit(type, payload) {
    (listeners[type] || []).forEach((fn) => fn(payload));
  }

  async function getJson(path) {
    const res = await fetch(backend + path);
    if (!res.ok) throw new Error(`${path} -> ${res.status}`);
    return res.json();
  }

  async function postJson(path, body) {
    const res = await fetch(backend + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${path} -> ${res.status}`);
    return res.json();
  }

  function connectWebSocket() {
    const wsUrl = backend.replace(/^http/, "ws") + "/ws";
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        emit(msg.type, msg.payload);
      } catch (e) {
        console.warn("Bad WS message", e);
      }
    };
    ws.onclose = () => setTimeout(connectWebSocket, 1500); // naive reconnect
    return ws;
  }

  // Resolve a backend-relative preview URL to an absolute origin URL.
  function assetUrl(relativeUrl) {
    return backend + relativeUrl;
  }

  window.api = {
    backend,
    on,
    getGpu: () => getJson("/gpu"),
    getModels: (installed) =>
      getJson(installed ? "/models?installed=true" : "/models"),
    getDevices: () => getJson("/devices"),
    setBaseFile: (path) => postJson("/file/base", { path }),
    appendFile: (path) => postJson("/file/append", { path }),
    listFiles: () => getJson("/files"),
    getPreview: (fileId) => getJson(`/preview/${fileId}`),
    runModel: (req) => postJson("/run", req),
    interrupt: () => postJson("/interrupt", {}),
    assetUrl,
    connectWebSocket,
  };
})();
