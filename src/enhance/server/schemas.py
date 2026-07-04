"""Pydantic DTOs exchanged between the Python backend and the Electron renderer.

These mirror the metadata the Qt UI read directly off `File` / `Operation` /
`Mask` / model dicts. Raw numpy arrays (images, mask arrays) are never serialized
here; they are delivered as preview images from the static cache mount.
"""

from typing import List, Optional

from pydantic import BaseModel


class GpuStats(BaseModel):
    present: bool
    utilization: Optional[float] = None  # 0..1
    memoryTotalGb: Optional[float] = None
    memoryAvailableGb: Optional[float] = None
    preferredDevice: str = "cpu"


class SetBaseFileRequest(BaseModel):
    path: str


class OperationInfo(BaseModel):
    index: int
    operationType: Optional[str] = None  # sharpen | denoise | upscale
    model: Optional[str] = None
    strength: Optional[float] = None  # 0..1, None if not applicable
    supportsStrength: bool = False
    scale: Optional[float] = None
    maskLabels: List[str] = []


class FileInfo(BaseModel):
    id: str
    kind: str = "input"  # base | input | output
    basename: Optional[str] = None
    path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitDepth: Optional[int] = None
    saved: bool = False
    operations: List[OperationInfo] = []


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


class StrengthRequest(BaseModel):
    fileId: str
    opIndex: int
    strength: float  # 0..1
