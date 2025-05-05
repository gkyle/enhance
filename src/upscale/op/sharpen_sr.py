import os
import cv2
import json
import torch

from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.archs.srresnet_arch import MSRResNet
from basicsr.archs.swinir_arch import SwinIR
# from Restormer.basicsr.models.archs.restormer_arch import Restormer
from basicsr_plus.archs.dat_arch import DAT
from basicsr_plus.archs.span_arch import SPAN

from upscale.app import Operation
from upscale.lib.file import DownscaleOperation, File, OutputFile
# from upscale.models.fpn_inception import FPNInception
from upscale.lib.util import Observable
from upscale.models.maxim import MAXIM_dns_3s
from upscale.op.simple_tile_processor import TileProcessor

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
        elif self.config["model_type"] == "SPAN":
            params = self.config["model_params"]
            model = SPAN(**params)
            scale = self.config["model_params"]["upscale"]
        elif self.config["model_type"] == "SwinIR":
            model = SwinIR(**self.config["model_params"])
            scale = self.config["model_params"]["upscale"]
            self.tileSize = self.config["model_params"]["img_size"]
            self.halfPrecision = False
            self.padToWindowSize = self.config["model_params"]["window_size"]
        # elif self.config["model_type"] == "FPNInception":
        #    model = FPNInception(**self.config["model_params"])
        #    scale = 1
        #    self.padToWindowSize = 128
        # elif self.config["model_type"] == "Restormer":
        #    scale = 1
        #    params = self.config["model_params"]
        #    if "real_denoising" in self.modelName:
        #        params['LayerNorm_type'] = 'BiasFree'
        #    model = Restormer(**params)
        # elif self.config["model_type"] == "Maxim":
        #    scale = 1
        #    self.tileSize = 1024
        #    model = MAXIM_dns_3s(**self.config["model_params"])
        #    model.load_state_dict(torch.load(self.modelPath), strict=True)
        elif self.config["model_type"] == "DAT":
            model = DAT(**self.config["model_params"])
            scale = self.config["model_params"]["upscale"]
            model.eval()
        else:
            raise ValueError("Unsupported model type: " + self.config["model_type"])

        if not model is None and not self.config["model_type"] == "Maxim":
            params = torch.load(self.modelPath)
            # Most state dicts are saved with "params" as the key
            if "params" in params:
                params = params["params"]
            model.load_state_dict(params, strict=True)
            model.eval()

        return model, scale

    def sharpen(self, inFile: File):
        model, scale = self.loadModel()

        processor = TileProcessor(
            model=model,
            tile_size=self.tileSize,
            tile_pad=10,
            scale=scale,
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

        if scale > 1:
            outputFile.postops.append(DownscaleOperation(1/scale))

        outputFile.applyPostProcessAndSave()  # Apply any postprocess ops and save

        return outputFile
