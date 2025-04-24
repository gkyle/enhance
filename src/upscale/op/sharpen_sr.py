import os
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.archs.srresnet_arch import MSRResNet
from basicsr.archs.swinir_arch import SwinIR
import time
import json
from PIL import Image

from upscale.lib.util import Observable
from upscale.op.sharpen_sr_utils import TiledSRProcessor
from upscale.ui.common import saveToCache

DEFAULT_TILE_SIZE = 128


# Sharpen via super resolution model based on BasicSR
class SharpenBasicSR(Observable):
    def __init__(self, modelPath: str, useGpu: bool):
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

        self.tileSize = DEFAULT_TILE_SIZE
        self.halfPrecision = False
        self.padToWindowSize = 0

    def sharpen(self, imgPath, doBlur: bool = True, blurKernelSize: int = 5, doBlend: bool = True, blendFactor: float = 0.5):
        model = None

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
        else:
            raise ValueError("Unsupported model type: " + self.config["model_type"])

        upsampler = TiledSRProcessor(
            scale=scale,
            model_path=self.modelPath,
            model=model,
            tile=self.tileSize,
            tile_pad=10,
            pre_pad=0,
            half=self.halfPrecision,
            device=self.device,
            pad_to_window_size=self.padToWindowSize,
        )
        upsampler.setObserver(self)

        img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
        output, _ = upsampler.enhance(img, outscale=scale)
        pathExtra = "_" + self.modelName

        # Apply blur to upscaled image
        if doBlur:
            blurred = cv2.GaussianBlur(output, (blurKernelSize, blurKernelSize), 0)
            downscale = cv2.resize(blurred, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
            pathExtra += "_blurred_" + str(blurKernelSize)
        else:
            downscale = cv2.resize(output, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)

        outpath = saveToCache(downscale, os.path.basename(imgPath), pathExtra)

        # Copy EXIF data from base image
        # TODO: Fails for TIF images exported from LR with custom fields
        """
        try:
            exifBaseImg = Image.open(imgPath)
            exif = exifBaseImg.getexif()
            exifOutImage = Image.open(outpath)
            exifOutImage.save(outpath, exifBaseImg.format, exif=exif)
        except Exception as e:
            print("Error copying EXIF data:", e)
        """

        return outpath
