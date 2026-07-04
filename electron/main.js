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

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill();
});
