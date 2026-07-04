// Preload: exposes a minimal, safe API to the renderer over contextBridge.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("native", {
  openImage: () => ipcRenderer.invoke("dialog:openImage"),
});
