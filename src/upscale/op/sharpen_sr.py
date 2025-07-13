import os
import cv2
from upscale.app import Operation
from upscale.lib.file import DownscaleOperation, File, OutputFile
from upscale.lib.util import Observable
from upscale.op.simple_tile_processor import TileProcessor

from spandrel import ImageModelDescriptor, ModelLoader
import spandrel_extra_arches
spandrel_extra_arches.install()


# Sharpen via super resolution model based on BasicSR
class SharpenBasicSR(Observable):
    def __init__(self, modelPath: str, tileSize: int, tilePadding: int, maintainScale: bool, device: str):
        super().__init__()

        self.modelPath = modelPath
        self.device = device if device is not None else "cpu"

        fileBaseName = os.path.basename(modelPath)
        fileBaseName, _ = os.path.splitext(fileBaseName)
        modelDir = os.path.dirname(modelPath)
        dirBaseName = os.path.basename(modelDir)
        dirBaseName, _ = os.path.splitext(dirBaseName)
        self.modelName = dirBaseName + "_" + fileBaseName

        self.tileSize = tileSize
        self.tilePadding = tilePadding
        self.maintainScale = maintainScale

    def sharpen(self, inFile: File):
        model = ModelLoader().load_from_file(self.modelPath)
        assert isinstance(model, ImageModelDescriptor)

        processor = TileProcessor(
            model=model,
            tileSize=self.tileSize,
            tilePad=self.tilePadding,
            scale=model.scale,
            device=self.device,
            observer=self,
        )

        imgPath = inFile.path
        img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
        output = processor.process_image(img)
        if output is None:
            return None

        # TODO: Fix this signature
        outputFile = OutputFile(None, inFile, Operation.Sharpen, self.modelName)
        outputFile.saveImage(output)
        if self.maintainScale and model.scale > 1:
            outputFile.postops.append(DownscaleOperation(1/model.scale))
        outputFile.applyPostProcessAndSave()  # Apply any postprocess ops and save

        return outputFile
