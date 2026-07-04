"""FastAPI service wrapping the existing `App`.

First-commit scope: GET /gpu, GET /models, POST /file/base, GET /preview/{fileId},
and the /ws WebSocket. The existing App/op/lib backend is reused unchanged.

Run with:  uvicorn enhance.server.server:app --host 127.0.0.1 --port 8420
(cwd must be the repo root so models/ and .cache resolve correctly.)
"""

import asyncio
import contextlib
import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from enhance.lib.file import File
from enhance.server import preview as preview_mod
from enhance.server.events import gpu_stats_loop, hub
from enhance.server.jobs import job_queue
from enhance.server.schemas import (
    FileInfo,
    GpuStats,
    PreviewResponse,
    SetBaseFileRequest,
)
from enhance.server.static import mount_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_app():
    """Construct the App without letting it consume uvicorn's argv."""
    from enhance.app import App

    saved_argv = sys.argv
    try:
        sys.argv = [saved_argv[0]] if saved_argv else ["enhance-server"]
        return App()
    finally:
        sys.argv = saved_argv


def _gpu_stats(app: FastAPI) -> dict:
    gpu = app.state.app.gpuInfo
    return GpuStats(
        present=gpu.getGpuPresent(),
        utilization=gpu.getGpuUtilization(),
        memoryTotalGb=gpu.getGpuMemeoryTotal(),
        memoryAvailableGb=gpu.getGpuMemoryAvailable(),
        preferredDevice=gpu.getPreferredDevice(),
    ).model_dump()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app = _build_app()
    # Registry of file id -> File so the renderer can reference files by id.
    app.state.files: Dict[str, File] = {}
    if app.state.app.getBaseFile() is not None:
        app.state.files["base"] = app.state.app.getBaseFile()

    job_queue.start()
    hub.bind_loop(asyncio.get_running_loop())
    stats_task = asyncio.create_task(gpu_stats_loop(lambda: _gpu_stats(app)))
    try:
        yield
    finally:
        stats_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await stats_task
        preview_mod.clear_preview_cache()


app = FastAPI(title="Enhance AI backend", lifespan=lifespan)

# Localhost experiment: the Electron renderer loads index.html from disk and
# fetches this service cross-origin, so permit all origins for now.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mount_cache(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/gpu", response_model=GpuStats)
def get_gpu() -> GpuStats:
    return GpuStats(**_gpu_stats(app))


@app.get("/models")
def get_models(installed: bool = False) -> dict:
    return app.state.app.getModels(installed=installed)


@app.post("/file/base", response_model=FileInfo)
def set_base_file(req: SetBaseFileRequest) -> FileInfo:
    import os

    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File not found")

    file = app.state.app.setBaseFile(req.path)
    app.state.files["base"] = file
    return _file_info("base", file)


@app.get("/preview/{file_id}", response_model=PreviewResponse)
def get_preview(file_id: str, w: int | None = None, h: int | None = None) -> PreviewResponse:
    file = app.state.files.get(file_id)
    if file is None or file.path is None:
        raise HTTPException(status_code=404, detail="Unknown file id")

    try:
        url, pw, ph = preview_mod.generate_preview(file.path, max_w=w, max_h=h)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PreviewResponse(url=url, width=pw, height=ph)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await hub.connect(ws)
    try:
        # Push initial GPU stats immediately so the UI isn't blank until the tick.
        await ws.send_json({"type": "gpuStats", "payload": _gpu_stats(app)})
        while True:
            # We don't expect client messages yet; keep the socket open.
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)
    except Exception:
        hub.disconnect(ws)


def _file_info(file_id: str, file: File) -> FileInfo:
    width = height = bit_depth = None
    img = file.loadUnchanged() if file.path else None
    if img is not None:
        height, width = img.shape[:2]
        bit_depth = int("".join(ch for ch in img.dtype.name if ch.isdigit()) or 0)
    return FileInfo(
        id=file_id,
        basename=file.basename,
        path=file.path,
        width=width,
        height=height,
        bitDepth=bit_depth,
    )
