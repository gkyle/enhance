import os
import cv2
import numpy as np
from typing import List
from enhance.lib.file import File, OutputFile, Operation, Mask
from enhance.lib.util import Observable
from enhance.op.simple_tile_processor import TileProcessor

from spandrel import ImageModelDescriptor, ModelLoader
import spandrel_extra_arches

spandrel_extra_arches.install()


def combine_masks(masks: List[Mask]) -> np.ndarray:
    """Combine multiple masks into a single binary mask."""
    if not masks:
        return None

    # Separate masks by inversion state
    inside_masks = [m for m in masks if not m.inverted]
    outside_masks = [m for m in masks if m.inverted]

    # Determine shape from first mask
    shape = masks[0].mask.shape

    # Combine inside masks
    if inside_masks:
        combined = np.zeros(shape, dtype=np.float32)
        for mask in inside_masks:
            mask_arr = mask.mask.astype(np.float32)
            if mask_arr.max() > 1.0:
                mask_arr = mask_arr / mask_arr.max()
            combined = np.maximum(combined, mask_arr)
    else:
        # No inside masks, start with full image
        combined = np.ones(shape, dtype=np.float32)

    # Combine outside masks
    for mask in outside_masks:
        mask_arr = mask.mask.astype(np.float32)
        if mask_arr.max() > 1.0:
            mask_arr = mask_arr / mask_arr.max()
        # Invert this mask and AND with combined
        inverted_mask = 1.0 - mask_arr
        combined = np.minimum(combined, inverted_mask)

    return combined


class ModelRunner(Observable):

    def __init__(
        self,
        modelKey: str,
        tileSize: int,
        tilePadding: int,
        maintainScale: bool,
        device: str,
        modelRoot: str = "models/",
    ):
        super().__init__()

        self.modelKey = modelKey
        self.modelRoot = modelRoot
        self.modelPath = os.path.join(modelRoot, modelKey)
        self.device = device if device is not None else "cpu"

        fileBaseName = os.path.basename(self.modelPath)
        fileBaseName, _ = os.path.splitext(fileBaseName)
        modelDir = os.path.dirname(self.modelPath)
        dirBaseName = os.path.basename(modelDir)
        dirBaseName, _ = os.path.splitext(dirBaseName)
        self.modelName = dirBaseName + "_" + fileBaseName

        self.tileSize = tileSize
        self.tilePadding = tilePadding
        self.maintainScale = maintainScale

    def run(
        self,
        inFile: File,
        operation: Operation = Operation.Sharpen,
        masks: List[Mask] = None,
    ):
        model = ModelLoader().load_from_file(self.modelPath)
        assert isinstance(model, ImageModelDescriptor)

        # Combine masks if provided
        combinedMask = combine_masks(masks) if masks else None

        processor = TileProcessor(
            model=model,
            tileSize=self.tileSize,
            tilePad=self.tilePadding,
            scale=model.scale,
            device=self.device,
            observer=self,
            mask=combinedMask,
        )

        imgPath = inFile.path
        img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
        output = processor.process_image(img)
        if output is None:
            return None

        # Determine scale factor if maintaining original dimensions
        scaleFactor = None
        if self.maintainScale and model.scale > 1:
            scaleFactor = 1 / model.scale

        outputFile = OutputFile(None, inFile)
        modelOp = outputFile.addOperation(
            operation_type=operation,
            model=self.modelName,
            modelPath=self.modelKey,
            scale=scaleFactor,
            masks=masks,
        )

        # Save the raw model output for strength/scale adjustment
        if modelOp.supportsStrength():
            outputFile.saveRawModelOutput(output, modelOp)
            # Apply strength blending against the input image
            inputImg = cv2.imread(inFile.path, cv2.IMREAD_UNCHANGED)
            output = outputFile.applyStrengthBlending(output, modelOp, inputImg)

        # Apply scaling if needed
        output = outputFile.applyScale(output, modelOp)
        outputFile.saveImageToCache(output)

        return outputFile

    def runOnExisting(
        self,
        outputFile: OutputFile,
        operation: Operation = Operation.Sharpen,
        masks: List[Mask] = None,
    ):
        """Run model on an existing OutputFile and update it in place"""
        model = ModelLoader().load_from_file(self.modelPath)
        assert isinstance(model, ImageModelDescriptor)

        # Combine masks if provided
        combinedMask = combine_masks(masks) if masks else None

        processor = TileProcessor(
            model=model,
            tileSize=self.tileSize,
            tilePad=self.tilePadding,
            scale=model.scale,
            device=self.device,
            observer=self,
            mask=combinedMask,
        )

        imgPath = outputFile.path
        img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
        output = processor.process_image(img)
        if output is None:
            return None

        # Determine scale factor if maintaining original dimensions
        scaleFactor = None
        if self.maintainScale and model.scale > 1:
            scaleFactor = 1 / model.scale

        # Store the input path before adding operation (for strength blending)
        inputPath = outputFile.path

        # Add the operation to the existing file's operations list
        outputFile.addOperation(
            operation_type=operation,
            model=self.modelName,
            modelPath=self.modelKey,
            scale=scaleFactor,
            masks=masks,
        )

        # Get the operation we just added
        modelOp = outputFile.operations[-1]

        # Save the raw model output for strength/scale adjustment
        if modelOp.supportsStrength():
            outputFile.saveRawModelOutput(output, modelOp)
            # Apply strength blending against the previous output (result of prior operations)
            inputImg = cv2.imread(inputPath, cv2.IMREAD_UNCHANGED)
            output = outputFile.applyStrengthBlending(output, modelOp, inputImg)

        # Apply scaling if needed
        output = outputFile.applyScale(output, modelOp)

        # Save the (possibly blended/scaled) model output to cache
        outputFile.saveImageToCache(output)

        return outputFile
