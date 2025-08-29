from glob import glob
import json
import time
import logging
from enum import Enum
from typing import List
import os
import sys
from huggingface_hub import HfApi


from enhance.lib.util import Observable
from enhance.lib.file import File, InputFile, OutputFile

# Use deferred loading for torch and modules that use torch to reduce startup latency.
from deferred_import import deferred_import


logger = logging.getLogger(__name__)

torch = deferred_import("torch")
modelRunner = deferred_import("enhance.op.model_runner")

# Conditionally import mask generation and subject detection modules
DO_DETECT = False
try:
    import enhance.op.masks as generate_masks
    import enhance.op.florence as detect_subjects

    DO_DETECT = True
except ImportError as e:
    pass

HF_REPO_ID = "gkyle/enhance"
MODEL_CONFIG = "models.json"

class Operation(Enum):
    Sharpen = "sharpen"
    Denoise = "denoise"
    Upscale = "upscale"


class App:

    def __init__(self):
        self.baseFile: InputFile = None
        self.rawFiles: List[File] = []
        self.doDetect = DO_DETECT
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

        # environment settings
        # use bfloat16
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

        if torch.cuda.get_device_properties(0).major >= 8:
            # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

    def setBaseFile(self, path: str) -> InputFile:
        self.baseFile = InputFile(path)
        return self.baseFile

    def getBaseFile(self) -> InputFile:
        return self.baseFile

    def getFileList(self) -> List[File]:
        return self.rawFiles

    def clearFileList(self) -> None:
        self.rawFiles = []

    def appendFile(
        self, path: str, baseFile: InputFile = None, operation: Operation = None
    ) -> File:
        file = OutputFile(path, baseFile, operation)
        self.rawFiles.append(file)
        return file

    def removeFile(self, file: File) -> None:
        self.rawFiles.remove(file)

    def runModel(
        self,
        file: InputFile,
        modelName: str,
        progressBar,
        tileSize: int,
        tilePadding: int,
        maintainScale: bool,
        device: str,
    ) -> OutputFile:
        runner = modelRunner.ModelRunner(
            self.getModelPath() + modelName,
            tileSize,
            tilePadding,
            maintainScale,
            device,
        )
        runner.addObserver(progressBar)
        self.activeOperation = runner
        outputFile = runner.run(file)
        runner.removeObserver(progressBar)
        if outputFile is None:
            return None
        self.rawFiles.append(outputFile)
        return outputFile

    def runAutoMask(self, file: InputFile, progressBar):
        if self.doDetect:
            device = self.getGpuNames()[0][0] if self.getGpuPresent() else "cpu"
            generateMasksOp = generate_masks.GenerateMasks(device)
            generateMasksOp.addObserver(progressBar)
            self.activeOperation = generateMasksOp
            success = generateMasksOp.run(file)
            generateMasksOp.removeObserver(progressBar)

    def runDetectSubjects(self, file: InputFile, progressBar):
        if self.doDetect:
            device = self.getGpuNames()[0][0] if self.getGpuPresent() else "cpu"
            detectSubjects = detect_subjects.GenerateLabels(device)
            detectSubjects.addObserver(progressBar)
            self.activeOperation = detectSubjects
            result = detectSubjects.detect(file)
            detectSubjects.removeObserver(progressBar)
            return result

    def interruptOperation(self):
        if self.activeOperation:
            self.activeOperation.requestInterrupt()

    def getGpuNames(self):
        try:
            if torch.backends.mps.is_available():
                return [["mps", "Apple Silicon GPU (MPS)"]]
            if torch.cuda.is_available():
                return [
                    [f"cuda:{i}", torch.cuda.get_device_name(i)]
                    for i in range(torch.cuda.device_count())
                ]
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

    def getModelPath(self) -> str:
        return os.path.join("models/")

    def getModels(self, installed=False):
        modelListPath = self.getModelPath() + MODEL_CONFIG
        with open(modelListPath, "r") as f:
            models = json.load(f)
        if installed:
            models = {
                path: model for path, model in models.items() if model.get("installed")
            }
        return models

    def storeModels(self, models):
        modelListPath = self.getModelPath() + MODEL_CONFIG
        with open(modelListPath, "w") as f:
            json.dump(models, f, indent=4)

    def fetchFile(self, path):
        modelInstallPath = self.getModelPath()
        hf_api_client = HfApi()
        hf_api_client.list_repo_files(HF_REPO_ID)
        hf_api_client.hf_hub_download(
            repo_id=HF_REPO_ID, filename=path, local_dir=modelInstallPath
        )

    def fetchModel(self, path):
        self.fetchFile(path)

        # Save the updated local models list
        models = self.getModels()
        if path in models:
            models[path]["installed"] = True
            self.storeModels(models)

    def refreshModelList(self):
        existingModels = self.getModels()
        self.fetchFile(MODEL_CONFIG)
        refreshedModels = self.getModels()
        for modelName, modelData in refreshedModels.items():
            if modelName not in existingModels:
                modelData["installed"] = True
            else:
                modelData["installed"] = existingModels[modelName].get(
                    "installed", False
                )
        self.storeModels(refreshedModels)

    def hasUnsavedChanges(self):
        for file in self.rawFiles:
            if isinstance(file, OutputFile) and not file.saved:
                return True
        return False

    # Clear cache files older than 7 days
    def clearCacheExpiredFiles(self):
        rootPath = os.getcwd() + "/.cache/"
        files = glob(rootPath + "*")
        for file in files:
            file_mod_time = os.path.getmtime(file)
            if file_mod_time < (time.time() - 60 * 60 * 24 * 7):
                try:
                    os.remove(file)
                except Exception as e:
                    logger.warning(f"Error removing file {file}: {e}")


def toGB(bytes):
    return bytes / (1024 * 1024 * 1024)
