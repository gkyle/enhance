"""FastAPI service wrapping the existing `App`.

First-commit scope: GET /gpu, GET /models, POST /file/base, GET /preview/{fileId},
and the /ws WebSocket. The existing App/op/lib backend is reused unchanged.

Run with:  uvicorn enhance.server.server:app --host 127.0.0.1 --port 8420
(cwd must be the repo root so models/ and .cache resolve correctly.)
"""

import asyncio
import contextlib
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from enhance.lib.file import File, InputFile, Operation, OutputFile
from enhance.server import preview as preview_mod
from enhance.server.events import gpu_stats_loop, hub
from enhance.server.jobs import job_queue
from enhance.server.schemas import (
    FileInfo,
    GpuStats,
    OperationInfo,
    PreviewResponse,
    RunRequest,
    RunResponse,
    SetBaseFileRequest,
    StrengthRequest,
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
    app.state.file_counter = 0
    app.state.job_counter = 0
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


@app.get("/devices")
def get_devices() -> list[dict]:
    """Available inference devices: cpu plus any detected GPUs."""
    devices = [{"id": "cpu", "name": "CPU"}]
    for gpu_id, name in app.state.app.gpuInfo.getGpuNames():
        devices.append({"id": gpu_id, "name": f"{name} ({gpu_id})"})
    return devices


@app.post("/file/base", response_model=FileInfo)
def set_base_file(req: SetBaseFileRequest) -> FileInfo:
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File not found")

    file = app.state.app.setBaseFile(req.path)
    app.state.files["base"] = file
    return _file_info("base", file)


@app.post("/file/append", response_model=FileInfo)
def append_file(req: SetBaseFileRequest) -> FileInfo:
    """Register an additional image the renderer can use as a compare file.

    Viewer-only concept for now; the operation pipeline (Phase 3+) manages its
    own output files via `App`.
    """
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File not found")

    file = InputFile(req.path)
    app.state.file_counter += 1
    fid = f"f{app.state.file_counter}"
    app.state.files[fid] = file
    return _file_info(fid, file)


@app.get("/files", response_model=list[FileInfo])
def list_files() -> list[FileInfo]:
    return [_file_info(fid, f) for fid, f in app.state.files.items()]


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


_OPERATIONS = {
    "sharpen": Operation.Sharpen,
    "denoise": Operation.Denoise,
    "upscale": Operation.Upscale,
}


class ProgressForwarder:
    """Observer forwarding `Observable` notifications to the WebSocket hub.

    Matches the `Observable.notifyObservers` callback signature and replaces the
    Qt `ProgressBarUpdater.tick`. Runs on the job worker thread, so it uses the
    threadsafe broadcast.
    """

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id

    def __call__(self, total, increment, count, done, data, status_message):
        hub.broadcast_threadsafe(
            {
                "type": "progress",
                "payload": {
                    "jobId": self.job_id,
                    "total": total,
                    "count": count,
                    "done": bool(done),
                    "statusMessage": status_message,
                },
            }
        )


@app.post("/run", response_model=RunResponse)
def run_model(req: RunRequest) -> RunResponse:
    target = app.state.files.get(req.fileId)
    if target is None or target.path is None:
        raise HTTPException(status_code=404, detail="Unknown file id")

    operation = _OPERATIONS.get(req.operation.lower())
    if operation is None:
        raise HTTPException(status_code=400, detail=f"Unknown operation: {req.operation}")

    app.state.job_counter += 1
    job_id = f"job{app.state.job_counter}"
    label = f"{req.operation.capitalize()}: {req.modelKey}"
    device = req.device or "cpu"

    def work() -> None:
        forwarder = ProgressForwarder(job_id)

        # Determine the output file to run on. Operations chain onto an existing
        # OutputFile; running on an InputFile (base or external) first creates a
        # fresh OutputFile copy, mirroring the Qt createOutputFile flow.
        if isinstance(target, OutputFile):
            output = target
            out_id = req.fileId
        else:
            output = app.state.app.createOutputFile(target)
            if output is None:
                hub.broadcast_threadsafe(
                    {"type": "runError", "payload": {"jobId": job_id, "message": "Could not create output file"}}
                )
                return
            app.state.app.rawFiles.append(output)
            app.state.file_counter += 1
            out_id = f"o{app.state.file_counter}"
            app.state.files[out_id] = output
            hub.broadcast_threadsafe(
                {"type": "fileAppended", "payload": _file_info(out_id, output).model_dump()}
            )

        try:
            result = app.state.app.runModelOnExisting(
                output,
                req.modelKey,
                forwarder,
                req.tileSize,
                req.tilePadding,
                req.maintainScale,
                device,
                operation,
                masks=None,
            )
        except Exception as e:
            logger.exception("Run failed")
            hub.broadcast_threadsafe(
                {"type": "runError", "payload": {"jobId": job_id, "message": str(e)}}
            )
            raise

        if result is None:
            hub.broadcast_threadsafe(
                {"type": "runError", "payload": {"jobId": job_id, "message": "No output produced"}}
            )
            return

        hub.broadcast_threadsafe(
            {
                "type": "runComplete",
                "payload": {"jobId": job_id, "file": _file_info(out_id, output).model_dump()},
            }
        )

    job_queue.submit(work, label=label, device=device)
    return RunResponse(jobId=job_id)


@app.post("/operation/strength", response_model=FileInfo)
def set_strength(req: StrengthRequest) -> FileInfo:
    """Adjust one operation's strength and re-blend the chain (no model rerun)."""
    file = app.state.files.get(req.fileId)
    if not isinstance(file, OutputFile):
        raise HTTPException(status_code=404, detail="Not an output file")
    if req.opIndex < 0 or req.opIndex >= len(file.operations):
        raise HTTPException(status_code=400, detail="Invalid operation index")

    op = file.operations[req.opIndex]
    if not op.supportsStrength():
        raise HTTPException(status_code=400, detail="Operation has no strength")

    op.strength = max(0.0, min(1.0, req.strength))
    if not file.reapplyStrength(op):
        raise HTTPException(status_code=500, detail="Failed to re-apply strength")
    return _file_info(req.fileId, file)


@app.delete("/file/{file_id}")
def delete_file(file_id: str) -> dict:
    file = app.state.files.pop(file_id, None)
    if file is None:
        raise HTTPException(status_code=404, detail="Unknown file id")
    try:
        app.state.app.removeFile(file)
    except ValueError:
        pass
    return {"status": "ok"}


@app.post("/interrupt")
def interrupt() -> dict:
    app.state.app.interruptOperation()
    return {"status": "ok"}


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

    if file_id == "base":
        kind = "base"
    elif isinstance(file, OutputFile):
        kind = "output"
    else:
        kind = "input"

    operations: list[OperationInfo] = []
    if isinstance(file, OutputFile):
        for idx, op in enumerate(file.operations):
            operations.append(
                OperationInfo(
                    index=idx,
                    operationType=op.operation_type.value if op.operation_type else None,
                    model=op.model,
                    strength=op.strength if op.supportsStrength() else None,
                    supportsStrength=op.supportsStrength(),
                    scale=op.scale,
                    maskLabels=[m.uniqueLabel for m in op.masks],
                )
            )

    return FileInfo(
        id=file_id,
        kind=kind,
        basename=file.basename,
        path=file.path,
        width=width,
        height=height,
        bitDepth=bit_depth,
        saved=getattr(file, "saved", False),
        operations=operations,
    )
