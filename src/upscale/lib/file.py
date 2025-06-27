from enum import Enum
import os
import time
from typing import List

import cv2
import numpy as np

from upscale.ui.common import write16bitTiff, write8bitFile


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

    def setPath(self, path):
        self.path = path
        self.basename = os.path.basename(path) if path else None

    def loadUnchanged(self):
        return cv2.imread(self.path, cv2.IMREAD_UNCHANGED)


class InputFile(File):

    def __init__(self, path):
        super().__init__(path)


class PostProcessOperationDeprecated(Enum):
    Blur = "Blur"
    Downscale = "Downscale"
    Blend = "Blend"


class PostProcessOperation():
    def execute(self, img, file: File):
        raise NotImplementedError("Not implemented")

    def getPathExtra(self):
        raise NotImplementedError("Not implemented")


class OutputFile(File):

    def __init__(self, path, baseFile: File, operation=None, model=None, postprocess: dict = None):
        super().__init__(path)

        self.baseFile = baseFile
        self.operation = operation
        self.model = model
        self.origPath = path
        self.postops: List[PostProcessOperation] = []

    def applyPostProcessAndSave(self):
        img = cv2.imread(self.origPath, cv2.IMREAD_UNCHANGED)
        for postop in self.postops:
            if isinstance(postop, PostProcessOperation):
                img = postop.execute(img, self)
            else:
                raise ValueError("Invalid post process operation")
        self.saveImage(img)

    def saveImage(self, img):
        # Determine path based on applied operations
        rootPath = os.getcwd() + "/.cache/"
        baseName = os.path.basename(self.baseFile.path)
        base, ext = os.path.splitext(baseName)
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        pathExtra = f"_{self.operation.value}_{self.model}"
        pathExtra = pathExtra + "".join(list(map(lambda x: x.getPathExtra(), self.postops)))

        outpath = os.path.join(rootPath, base + pathExtra + "_" + timestamp + ext)

        print(f'Saving {img.dtype} image to cache: {outpath}')
        if img.dtype == np.uint16 or img.dtype == "uint16":
            write16bitTiff(img, self.baseFile.path, outpath)
        else:
            write8bitFile(img, self.baseFile.path, outpath)

        self.setPath(outpath)
        return outpath

    def setPath(self, path):
        super().setPath(path)
        if self.origPath is None:
            self.origPath = path


class DownscaleOperation(PostProcessOperation):
    def __init__(self, scale: float):
        super().__init__()
        self.scale = scale
        self.method = cv2.INTER_AREA
        self.editable = False

    def execute(self, img, file: OutputFile):
        img = cv2.resize(img, None, fx=self.scale, fy=self.scale, interpolation=self.method)
        return img

    def getPathExtra(self):
        return f"_downscale_{int(1/self.scale)}X"


class BlendOperation(PostProcessOperation):
    def __init__(self, factor: float):
        super().__init__()
        self.factor = factor
        self.editable = True

    def execute(self, img, file: OutputFile):
        baseImg = cv2.imread(file.baseFile.path, cv2.IMREAD_UNCHANGED)
        blendedImg = cv2.addWeighted(baseImg, self.factor, img, 1 - self.factor, 0)
        return blendedImg

    def getPathExtra(self):
        return f"_blend_{self.factor}"


class BlurOperation(PostProcessOperation):
    def __init__(self, kernelSize: int):
        super().__init__()
        self.kernelSize = kernelSize
        self.editable = True

    def execute(self, img, file: OutputFile):
        return cv2.GaussianBlur(img, (self.kernelSize, self.kernelSize), 0)

    def getPathExtra(self):
        return f"_blur_{self.kernelSize}"
