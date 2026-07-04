// Electron main process: spawns the Python backend and opens the renderer.
// Experiment scope only — no packaging, health-check/restart, or hardening yet.

const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const net = require("net");
const http = require("http");

const REPO_ROOT = path.resolve(__dirname, "..");

let backendProcess = null;
let backendPort = null;
let mainWindow = null;
// Set once the user confirms quitting with unsaved changes (or none exist), so
// the async close handler can let the second close() through synchronously.
let allowClose = false;

function findFreePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.unref();
    srv.on("error", reject);
    srv.listen(0, "127.0.0.1", () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

function waitForBackend(port, timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(
        { host: "127.0.0.1", port, path: "/health", timeout: 1000 },
        (res) => {
          res.destroy();
          if (res.statusCode === 200) resolve();
          else retry();
        }
      );
      req.on("error", retry);
      req.on("timeout", () => {
        req.destroy();
        retry();
      });
    };
    const retry = () => {
      if (Date.now() > deadline) reject(new Error("Backend did not start in time"));
      else setTimeout(attempt, 500);
    };
    attempt();
  });
}

function spawnBackend(port) {
  // Uses the project's virtualenv python via `uv run`. Falls back to `python`
  // if uv is unavailable in the future; experiment assumes `uv` is present.
  const args = [
    "run",
    "uvicorn",
    "enhance.server.server:app",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
  ];
  const proc = spawn("uv", args, {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHONPATH: path.join(REPO_ROOT, "src") },
    stdio: ["ignore", "pipe", "pipe"],
  });
  proc.stdout.on("data", (d) => process.stdout.write(`[backend] ${d}`));
  proc.stderr.on("data", (d) => process.stderr.write(`[backend] ${d}`));
  proc.on("exit", (code) => console.log(`[backend] exited with code ${code}`));
  return proc;
}

async function createWindow() {
  backendPort = await findFreePort();
  backendProcess = spawnBackend(backendPort);
  await waitForBackend(backendPort);

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    backgroundColor: "#444444",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Pass the backend origin to the renderer via query string.
  const url = `file://${path.join(__dirname, "renderer", "index.html")}?backend=http://127.0.0.1:${backendPort}`;
  mainWindow.loadURL(url);

  // Unsaved-changes quit guard (ports the Qt closeEvent QMessageBox). Ask the
  // backend whether any output file is unsaved; if so, confirm before closing.
  mainWindow.on("close", (event) => {
    if (allowClose) return;
    event.preventDefault();
    confirmClose();
  });
}

function backendGetJson(pathname) {
  return new Promise((resolve, reject) => {
    const req = http.get(
      { host: "127.0.0.1", port: backendPort, path: pathname, timeout: 2000 },
      (res) => {
        let body = "";
        res.on("data", (d) => (body += d));
        res.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
}

async function confirmClose() {
  let unsaved = false;
  try {
    const res = await backendGetJson("/has-unsaved");
    unsaved = !!(res && res.unsaved);
  } catch {
    unsaved = false; // if we can't ask, don't block quitting
  }

  if (unsaved) {
    const { response } = await dialog.showMessageBox(mainWindow, {
      type: "warning",
      buttons: ["Cancel", "Quit Without Saving"],
      defaultId: 0,
      cancelId: 0,
      title: "Unsaved Changes",
      message: "You have unsaved files.",
      detail: "Do you really want to quit? Unsaved output images will be lost.",
    });
    if (response !== 1) return; // Cancel: keep the window open
  }

  allowClose = true;
  if (mainWindow) mainWindow.close();
}

// Native file open dialog (replaces QFileDialog).
ipcMain.handle("dialog:openImage", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [{ name: "Images", extensions: ["jpg", "jpeg", "tif", "tiff", "png"] }],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  return result.filePaths[0];
});

// Native save dialog for exporting an output image (replaces QFileDialog save).
ipcMain.handle("dialog:saveImage", async (_event, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: defaultName || undefined,
    filters: [{ name: "Images", extensions: ["png", "jpg", "jpeg", "tif", "tiff"] }],
  });
  if (result.canceled || !result.filePath) return null;
  return result.filePath;
});

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill();
});
