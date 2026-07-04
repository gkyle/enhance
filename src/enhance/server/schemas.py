"""Pydantic DTOs exchanged between the Python backend and the Electron renderer.

These mirror the metadata the Qt UI read directly off `File` / `Operation` /
`Mask` / model dicts. Raw numpy arrays (images, mask arrays) are never serialized
here; they are delivered as preview images from the static cache mount.
"""

from typing import Optional

from pydantic import BaseModel


class GpuStats(BaseModel):
    present: bool
    utilization: Optional[float] = None  # 0..1
    memoryTotalGb: Optional[float] = None
    memoryAvailableGb: Optional[float] = None
    preferredDevice: str = "cpu"


class SetBaseFileRequest(BaseModel):
    path: str


class FileInfo(BaseModel):
    id: str
    basename: Optional[str] = None
    path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitDepth: Optional[int] = None


class PreviewResponse(BaseModel):
    url: str
    width: int
    height: int


class RunRequest(BaseModel):
    fileId: str = "base"
    modelKey: str
    operation: str = "sharpen"  # sharpen | denoise | upscale
    tileSize: int = 512
    tilePadding: int = 32
    maintainScale: bool = True
    device: Optional[str] = None  # None -> cpu


class RunResponse(BaseModel):
    jobId: str
