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
    masks: Optional[List["MaskSelection"]] = None


class MaskSelection(BaseModel):
    index: int
    inverted: bool = False


class RunResponse(BaseModel):
    jobId: str


class StrengthRequest(BaseModel):
    fileId: str
    opIndex: int
    strength: float  # 0..1


class SaveFileRequest(BaseModel):
    targetPath: str


class MaskInfo(BaseModel):
    index: int
    label: str
    uniqueLabel: str
    score: Optional[float] = None
    box: List[float] = []  # [x1, y1, x2, y2]
    overlayUrl: Optional[str] = None


class TaskInfo(BaseModel):
    id: int
    label: str
    device: Optional[str] = None
    status: str
    scheduleTime: float
    latency: Optional[float] = None


class AutoMaskRequest(BaseModel):
    fileId: str = "base"


# Resolve the forward reference RunRequest -> MaskSelection.
RunRequest.model_rebuild()

