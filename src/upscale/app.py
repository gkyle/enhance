from upscale.lib.util import Observable
from upscale.lib.file import File, InputFile, OutputFile
from enum import Enum
from typing import List, Any, Dict
import jsonpickle
import os
import sys

# Use deferred loading for torch and modules that use torch to reduce startup latency.
from deferred_import import deferred_import
torch = deferred_import('torch')


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
                    self.setBaseFile(dirname + "/" + files[0])
                else:
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

    def listModels(self, excludefilters=[]) -> List[str]:
        models = []
        for root, dirs, files in os.walk("models"):
            for file in files:
                if file.endswith(".pth"):
                    path = os.path.join(root, file)
                    if any(filter in path for filter in excludefilters):
                        continue
                    models.append(os.path.join(root, file))
        models = sorted(models)
        return models

    # TODO: Support variable tile size
    def doSharpen(self, file: InputFile, modelName: str, progressBar, tileSize: int, tilePadding: int, maintainScale: bool, device: str) -> OutputFile:
        sharpenSR = sharpen_sr.SharpenBasicSR(modelName, tileSize, tilePadding, maintainScale, device)
        sharpenSR.addObserver(progressBar)
        self.activeOperation = sharpenSR
        outputFile = sharpenSR.sharpen(file)
        sharpenSR.removeObserver(progressBar)
        if outputFile is None:
            return None
        self.rawFiles.append(outputFile)
        return outputFile

    def doInterruptOperation(self):
        if self.activeOperation:
            self.activeOperation.requestInterrupt()

    def getGpuNames(self):
        try:
            if torch.backends.mps.is_available():
                return [["mps", "Apple Silicon GPU (MPS)"]]
            if torch.cuda.is_available():
                return [[f"cuda:{i}", torch.cuda.get_device_name(i)] for i in range(torch.cuda.device_count())]
        except Exception as e:
            pass
        return []

    def getGpuStats(self):
        try:
            if torch.backends.mps.is_available():
                # MPS does not provide memory stats
                return None
            if torch.cuda.is_available():
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return int(toGB(free_bytes)), int(toGB(total_bytes))
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
    return bytes / (1024 * 1024 * 1024)
