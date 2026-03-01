from enum import Enum
import hashlib
import os
import shutil
import time
from typing import List

import cv2
import numpy as np
import logging

from enhance.ui.common import writeTiffFile, writeFile

logger = logging.getLogger(__name__)


# Leave headroom below Windows MAX_PATH (260) for temp-file suffixes
# that libraries like tifftools append during writes.
_MAX_FILENAME_PATH = 240


class Unpickle:
    # forces reinitialization of instance during unpickling so that fields that weren't present at pickling time are present at run time.
    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state: dict):
        self.__init__()
        self.__dict__.update(state)


class File(Unpickle):

    def __init__(self, path):
        super().__init__()
        self.basename = os.path.basename(path) if path else None
        self.path = path
        self.timestamp = 0
        self.saved = False

    def setPath(self, path):
        self.path = path
        self.basename = os.path.basename(path) if path else None

    def loadUnchanged(self):
        return cv2.imread(self.path, cv2.IMREAD_UNCHANGED)


class Mask:

    def __init__(
        self,
        score: float,
        label: str,
        mask: np.ndarray,
        box: tuple,
        uniqueLabel: str = None,
        inverted: bool = False,
    ):
        self.score = score
        self.label = label
        self.mask = mask
        self.box = box
        # Unique label for this mask instance (e.g., "person_1", "person_2")
        self.uniqueLabel = uniqueLabel if uniqueLabel else label
        self.inverted = inverted


class Label:
    def __init__(self, label: str, box: tuple):
        self.label = label
        self.box = box


class InputFile(File):
    def __init__(self, path):
        super().__init__(path)
        self.masks: list[Mask] = []
        self.labels: list[Label] = []

    def addMask(self, mask: Mask):
        """Add a mask with a unique label"""
        # Count existing masks with the same base label
        count = sum(1 for m in self.masks if m.label == mask.label)
        if count > 0:
            mask.uniqueLabel = f"{mask.label}_{count + 1}"
        else:
            # Check if there's already a mask with this label
            existing = [m for m in self.masks if m.label == mask.label]
            if existing:
                # Rename the first one
                existing[0].uniqueLabel = f"{mask.label}_1"
                mask.uniqueLabel = f"{mask.label}_2"
            else:
                mask.uniqueLabel = mask.label
        self.masks.append(mask)


class Operation(Enum):
    Sharpen = "sharpen"
    Denoise = "denoise"
    Upscale = "upscale"


class AppliedOperation:
    """Represents a model operation (sharpen/denoise/upscale) applied to an OutputFile"""

    DEFAULT_STRENGTH = 0.8  # 80% strength by default

    def __init__(
        self,
        operation_type: Operation = None,
        model: str = None,
        modelPath: str = None,
        strength: float = None,
        scale: float = None,
        masks: List["Mask"] = None,
    ):
        self.operation_type = operation_type
        self.model = model  # Display name
        self.modelPath = modelPath  # Original path for re-running
        # Scale factor (e.g., 0.5 means downscale 2X to maintain original dimensions)
        self.scale = scale
        # Strength (0.0-1.0, where 1.0 = full effect)
        if strength is None:
            if operation_type in (Operation.Sharpen, Operation.Denoise):
                self.strength = self.DEFAULT_STRENGTH
            elif (
                operation_type == Operation.Upscale
                and scale is not None
                and scale < 1.0
            ):
                self.strength = self.DEFAULT_STRENGTH
            else:
                self.strength = strength
        else:
            self.strength = strength
        # Path to the raw (unblended, unscaled) model output
        self.rawOutputPath: str = None
        # List of masks to apply to this operation (only process within masked regions)
        self.masks: List["Mask"] = masks if masks is not None else []

    def getPathExtra(self) -> str:
        if self.operation_type and self.model:
            base = f"_{self.operation_type.value}_{self.model}"
            # Include strength in path if not 100%
            if self.strength is not None and self.strength < 1.0:
                base += f"_s{int(self.strength * 100)}"
            # Include scale in path if downscaling
            if self.scale is not None and self.scale < 1.0:
                base += f"_d{int(1/self.scale)}X"
            # Include mask labels if any
            if self.masks:
                # Separate inside and outside masks for path naming
                inside_masks = [m for m in self.masks if not m.inverted]
                outside_masks = [m for m in self.masks if m.inverted]
                if inside_masks:
                    inside_labels = "_".join(m.uniqueLabel.replace(" ", "-") for m in inside_masks)
                    base += f"_m{inside_labels}"
                if outside_masks:
                    outside_labels = "_".join(m.uniqueLabel.replace(" ", "-") for m in outside_masks)
                    base += f"_minv{outside_labels}"
            return base
        return ""

    def supportsStrength(self) -> bool:
        if self.operation_type in (Operation.Sharpen, Operation.Denoise):
            return True
        if (
            self.operation_type == Operation.Upscale
            and self.scale is not None
            and self.scale < 1.0
        ):
            return True
        return False


class OutputFile(File):

    def __init__(self, path, baseFile: File):
        super().__init__(path)

        self.baseFile = baseFile
        self.origPath = path

        # List of model operations applied to this file
        self.operations: List[AppliedOperation] = []

    def getFirstOperation(self) -> AppliedOperation:
        """Get the first operation, or None if none exist"""
        return self.operations[0] if self.operations else None

    def getOperationIndex(self, operation: AppliedOperation) -> int:
        """Get the index of an operation, or -1 if not found"""
        for i, op in enumerate(self.operations):
            if op is operation:
                return i
        return -1

    def removeOperationsFrom(self, index: int):
        """Remove all operations from the given index onwards"""
        if index >= 0 and index < len(self.operations):
            self.operations = self.operations[:index]

    def addOperation(
        self,
        operation_type: Operation = None,
        model: str = None,
        modelPath: str = None,
        strength: float = None,
        scale: float = None,
        masks: List[Mask] = None,
    ) -> AppliedOperation:
        """Add an operation to this output file"""
        self.operations.append(
            AppliedOperation(
                operation_type=operation_type,
                model=model,
                modelPath=modelPath,
                strength=strength,
                scale=scale,
                masks=masks,
            )
        )

        return self.operations[-1]

    def applyScale(self, img, operation: AppliedOperation):
        """Apply scaling for a model operation (e.g., downscale to maintain original size)"""
        if operation.scale is None or operation.scale >= 1.0:
            return img

        scaled = cv2.resize(img, None, fx=operation.scale, fy=operation.scale, interpolation=cv2.INTER_AREA)
        return scaled

    def saveRawModelOutput(self, img, operation: AppliedOperation):
        """Save the raw (unblended) model output for later strength adjustment"""
        rootPath = os.path.normpath(os.path.join(os.getcwd(), ".cache"))
        if not os.path.exists(rootPath):
            os.makedirs(rootPath)
        baseName = os.path.basename(self.baseFile.path)
        base, ext = os.path.splitext(baseName)
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        # Save raw output with _raw suffix
        rawFilename = f"{base}_{operation.operation_type.value}_{operation.model}_raw_{timestamp}{ext}"
        rawFilename = _truncate_path(rootPath, rawFilename)
        rawPath = os.path.join(rootPath, rawFilename)

        logger.info(f"Saving raw model output to: {rawPath}")
        if ext.lower() in [".tif", ".tiff"]:
            writeTiffFile(img, self.baseFile.path, rawPath)
        else:
            writeFile(img, self.baseFile.path, rawPath)

        operation.rawOutputPath = rawPath
        return rawPath

    def applyStrengthBlending(self, img, operation: AppliedOperation, inputImg):
        if not operation.supportsStrength() or operation.strength is None or operation.strength >= 1.0:
            return img

        if inputImg is None:
            logger.warning("No input image for blending")
            return img

        # Resize input if dimensions don't match (e.g., after upscale)
        if inputImg.shape != img.shape:
            inputImg = cv2.resize(
                inputImg, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC
            )

        # Blend: result = strength * model_output + (1 - strength) * input
        strength = operation.strength
        blendedImg = cv2.addWeighted(img, strength, inputImg, 1 - strength, 0)
        return blendedImg

    def reapplyStrength(self, operation: AppliedOperation):
        """Reapply all operations with their current strengths.

        When any operation's strength changes, we need to reprocess all operations
        in sequence since later operations depend on the results of earlier ones.
        """
        # Start with the base file
        currentImg = cv2.imread(self.baseFile.path, cv2.IMREAD_UNCHANGED)
        if currentImg is None:
            logger.warning(f"Could not read base file: {self.baseFile.path}")
            return False

        # Process all operations in sequence
        for op in self.operations:
            if op.rawOutputPath is None or not os.path.exists(op.rawOutputPath):
                logger.warning(
                    f"Raw output not found for operation: {op.rawOutputPath}"
                )
                continue

            # Load this operation's raw output
            rawImg = cv2.imread(op.rawOutputPath, cv2.IMREAD_UNCHANGED)
            if rawImg is None:
                logger.warning(f"Could not read raw output: {op.rawOutputPath}")
                continue

            # Apply post processing
            blendedImg = self.applyStrengthBlending(rawImg, op, currentImg)
            blendedImg = self.applyScale(blendedImg, op)
            currentImg = blendedImg

        # Save the final result
        self.saveImageToCache(currentImg)
        return True

    def saveImageToCache(self, img):
        # Determine path based on applied operations
        rootPath = os.path.normpath(os.path.join(os.getcwd(), ".cache"))
        if not os.path.exists(rootPath):
            os.makedirs(rootPath)
        baseName = os.path.basename(self.baseFile.path)
        base, ext = os.path.splitext(baseName)
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        # Build path from all operations
        pathExtra = "".join(op.getPathExtra() for op in self.operations)

        filename = base + pathExtra + "_" + timestamp + ext
        filename = _truncate_path(rootPath, filename)
        outpath = os.path.join(rootPath, filename)

        logger.info(f"Saving {img.dtype} image to cache: {outpath}")
        if ext.lower() in [".tif", ".tiff"]:
            writeTiffFile(img, self.baseFile.path, outpath)
        else:
            writeFile(img, self.baseFile.path, outpath)

        self.setPath(outpath)
        self.saved = False
        return outpath

    # Copy cached img to the target directory
    def saveImage(self, targetDir):
        newPath = os.path.join(targetDir, os.path.basename(self.path))
        shutil.copyfile(self.path, newPath)
        self.saved = True

    def setPath(self, path):
        super().setPath(path)
        if self.origPath is None:
            self.origPath = path

def _truncate_path(directory: str, filename: str) -> str:
    """Truncate filename if the full path would exceed the safe limit."""
    directory = os.path.normpath(directory)
    full = os.path.join(directory, filename)
    if len(full) <= _MAX_FILENAME_PATH:
        return filename
    
    base, ext = os.path.splitext(filename)
    # 8-char hex hash for uniqueness
    digest = hashlib.md5(base.encode()).hexdigest()[:8]
    # How much space is available for the base name?
    # directory + separator + base + "_" + hash + extension
    overhead = len(directory) + 1 + 1 + len(digest) + len(ext)
    max_base = _MAX_FILENAME_PATH - overhead
    if max_base < 1:
        max_base = 1
    truncated = base[:max_base] + "_" + digest + ext
    return truncated