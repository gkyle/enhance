import cv2
from upscale.app import Operation
from upscale.lib.file import DownscaleOperation, File, OutputFile
from upscale.lib.util import Observable
from upscale.op.simple_tile_processor import TileProcessor

from spandrel import ImageModelDescriptor, ModelLoader
import spandrel_extra_arches


# Sharpen via super resolution model based on BasicSR
class SharpenBasicSR(Observable):
    def __init__(self, modelPath: str, tileSize: int, tilePadding: int, useGpu: bool):
        super().__init__()
        spandrel_extra_arches.install()

        self.modelPath = modelPath
        self.device = "cuda" if useGpu else "cpu"

        self.tileSize = tileSize
        self.tilePadding = tilePadding

    def sharpen(self, inFile: File):
        model = ModelLoader().load_from_file(self.modelPath)
        assert isinstance(model, ImageModelDescriptor)
        modelName = model.architecture.name
        print(f"Using model: {modelName} with scale {model.scale}")

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
        outputFile = OutputFile(None, inFile, Operation.Sharpen, modelName)
        outputFile.saveImage(output)

        if model.scale > 1:
            outputFile.postops.append(DownscaleOperation(1/model.scale))

        outputFile.applyPostProcessAndSave()  # Apply any postprocess ops and save

        return outputFile
