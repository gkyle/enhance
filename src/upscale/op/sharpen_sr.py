import os
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.archs.srresnet_arch import MSRResNet
from basicsr.archs.swinir_arch import SwinIR
import json
import torch

from upscale.models.fpn_inception import FPNInception
from upscale.lib.util import Observable
from upscale.op.simple_tile_processor import TileProcessor
from upscale.ui.common import saveToCache

DEFAULT_TILE_SIZE = 128


# Sharpen via super resolution model based on BasicSR
class SharpenBasicSR(Observable):
    def __init__(self, modelPath: str, tileSize: int, useGpu: bool):
        super().__init__()
        self.modelPath = modelPath
        self.useGpu = useGpu
        if useGpu:
            self.device = "cuda"
        else:
            self.device = "cpu"

        fileBaseName = os.path.basename(modelPath)
        fileBaseName, _ = os.path.splitext(fileBaseName)
        modelDir = os.path.dirname(modelPath)
        dirBaseName = os.path.basename(modelDir)
        dirBaseName, _ = os.path.splitext(dirBaseName)
        self.modelName = dirBaseName + "_" + fileBaseName

        configPath = os.path.join(modelDir, "config.json")
        self.config = json.load(open(configPath, "r"))

        self.tileSize = tileSize
        self.halfPrecision = False
        self.padToWindowSize = 0

    def loadModel(self):
        if self.config["model_type"] == "RRDBNet":
            model = RRDBNet(**self.config["model_params"])
            scale = self.config["model_params"]["scale"]
        elif self.config["model_type"] == "MSRResNet":
            model = MSRResNet(**self.config["model_params"])
            scale = self.config["model_params"]["upscale"]
        elif self.config["model_type"] == "SwinIR":
            model = SwinIR(**self.config["model_params"])
            scale = self.config["model_params"]["upscale"]
            self.tileSize = self.config["model_params"]["img_size"]
            self.halfPrecision = False
            self.padToWindowSize = self.config["model_params"]["window_size"]
        elif self.config["model_type"] == "FPNInception":
            model = FPNInception(**self.config["model_params"])
            scale = 1
            self.padToWindowSize = 128
        else:
            raise ValueError("Unsupported model type: " + self.config["model_type"])

        if not model is None:
            model.load_state_dict(torch.load(self.modelPath)['params'], strict=True)
            model.eval()

        return model, scale

    def sharpen(self, imgPath, doBlur: bool = True, blurKernelSize: int = 5, doBlend: bool = True, blendFactor: float = 0.5):
        model, scale = self.loadModel()

        processor = TileProcessor(
            model=model,
            tile_size=self.tileSize,
            tile_pad=10,
            scale=scale,
            device=self.device,
            observer=self,
        )

        img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
        output = processor.process_image(img)
        if output is None:
            return None
        pathExtra = "_" + self.modelName

        # Apply blur to upscaled image
        if doBlur:
            blurred = cv2.GaussianBlur(output, (blurKernelSize, blurKernelSize), 0)
            downscale = cv2.resize(blurred, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
            pathExtra += "_blurred_" + str(blurKernelSize)
        else:
            downscale = cv2.resize(output, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)

        outpath = saveToCache(downscale, imgPath, pathExtra)

        return outpath
