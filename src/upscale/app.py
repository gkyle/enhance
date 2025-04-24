from enum import Enum
from typing import List, Any, Dict
import jsonpickle
import os
import GPUtil
import sys

# Use deferred loading for torch and modules that use torch to reduce startup latency.
from deferred_import import deferred_import
torch = deferred_import('torch')

from upscale.lib.file import File, InputFile, OutputFile
from upscale.lib.util import Observable

sharpen_sr = deferred_import('upscale.op.sharpen_sr')

class Operation(Enum):
    Sharpen = "Sharpen"
    Upscale = "Upscale"


class App:

    def __init__(self):
        self.baseFile: InputFile = None
        self.rawFiles: List[File] = []
        if len(sys.argv) > 1:
            if os.path.exists(sys.argv[1]):
                if os.path.isdir(sys.argv[1]):
                    dirname = sys.argv[1]
                    files = os.listdir(sys.argv[1])
                    print("file:", dirname + "/" + files[0])
                    self.setBaseFile(dirname + "/" + files[0])
                else:
                    print("file:", sys.argv[1])
                    self.setBaseFile(sys.argv[1])
        if len(sys.argv) > 2:
            for i in range(2, len(sys.argv)):
                self.appendFile(sys.argv[i])

        self.activeOperation: Observable = None

    def setBaseFile(self, path: str) -> InputFile:
        self.baseFile = InputFile(path)
        return self.baseFile

    def getBaseFile(self) -> InputFile:
        return self.baseFile

    def getFileList(self) -> List[File]:
        return self.rawFiles

    def clearFileList(self) -> None:
        self.rawFiles = []

    def appendFile(self, path: str, baseFile: InputFile = None, operation: Operation = None) -> File:
        file = OutputFile(path, baseFile, operation)
        self.rawFiles.append(file)
        return file

    def removeFile(self, file: File) -> None:
        self.rawFiles.remove(file)

    def listModels(self) -> List[str]:
        models = []
        for root, dirs, files in os.walk("models"):
            for file in files:
                if file.endswith(".pth"):
                    models.append(os.path.join(root, file))
        models = sorted(models)
        return models

    def doSharpen(self, file: InputFile, modelName: str, doBlur: bool, blurKernelSize: int, doBlend: bool, blendFactor: float,  progressBar, useGpu: bool) -> OutputFile:
        sharpenSR = sharpen_sr.SharpenBasicSR(modelName, useGpu)
        sharpenSR.addObserver(progressBar)
        self.activeOperation = sharpenSR
        outpath = sharpenSR.sharpen(file.path, doBlur, blurKernelSize, doBlend, blendFactor)
        sharpenSR.removeObserver(progressBar)
        outfile = self.appendFile(outpath, None, Operation.Sharpen)
        return outfile

    def doInterruptOperation(self):
        if self.activeOperation:
            self.activeOperation.requestInterrupt()

    def getGpuStats(self):
        try:
            if torch.cuda.is_available():
                gpu = GPUtil.getGPUs()
                return int(toGB(gpu[0].memoryFree)), int(toGB(gpu[0].memoryTotal))
        except Exception as e:
            pass
        return None

    def getGpuPresent(self):
        try:
            if torch.cuda.is_available():
                return True
        except Exception as e:
            pass
        return False


def toGB(bytes):
    return bytes / (1024)
