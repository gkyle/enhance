from glob import glob
import json
import time
import logging
from enum import Enum
from typing import List
import os
import sys
import shutil
import time
import os

from huggingface_hub import HfApi


from enhance.lib.util import Observable
from enhance.lib.file import File, InputFile, OutputFile, Operation
from enhance.lib.gpu import GPUInfo

logger = logging.getLogger(__name__)

# Use deferred loading for torch and modules that use torch to reduce startup latency.
from deferred_import import deferred_import

torch = deferred_import("torch")
modelRunner = deferred_import("enhance.op.model_runner")

# Conditionally import mask generation and subject detection modules
DO_DETECT = False
try:
    import enhance.op.masks as generate_masks
    import enhance.op.florence as detect_subjects

    DO_DETECT = True
except ImportError as e:
    logger.warning(f"Optional detection modules not available: {e}")
    pass

HF_REPO_ID = "gkyle/enhance"
MODEL_CONFIG = "models.json"

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

        self.gpuInfo = GPUInfo()
        self.activeOperation: Observable = None

        # environment settings
        # use bfloat16
        torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

        try:
            if torch.cuda.get_device_properties(0).major >= 8:
                # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
        except:
            pass

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
        self, path: str, baseFile: InputFile = None
    ) -> File:
        file = OutputFile(path, baseFile)
        self.rawFiles.append(file)
        return file

    def removeFile(self, file: File) -> None:
        self.rawFiles.remove(file)

    def createOutputFile(self, baseFile: InputFile) -> OutputFile:
        """Create a new OutputFile from a base file, copying its image to cache"""

        # Create cache directory if needed
        cachePath = os.getcwd() + "/.cache/"
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)

        # Generate output path
        baseName = os.path.basename(baseFile.path)
        base, ext = os.path.splitext(baseName)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        outPath = os.path.join(cachePath, f"{base}_copy_{timestamp}{ext}")

        # Copy the base file to cache
        shutil.copyfile(baseFile.path, outPath)

        # Create OutputFile
        outputFile = OutputFile(outPath, baseFile)
        return outputFile

    def runModel(
        self,
        file: InputFile,
        modelKey: str,
        progressBar,
        tileSize: int,
        tilePadding: int,
        maintainScale: bool,
        device: str,
        operation: Operation = Operation.Sharpen,
        masks: list = None,
    ) -> OutputFile:
        runner = modelRunner.ModelRunner(
            modelKey,
            tileSize,
            tilePadding,
            maintainScale,
            device,
            modelRoot=self.getModelRoot(),
        )
        runner.addObserver(progressBar)
        self.activeOperation = runner
        outputFile = runner.run(file, operation, masks=masks)
        runner.removeObserver(progressBar)
        if outputFile is None:
            return None
        self.rawFiles.append(outputFile)
        return outputFile

    def runModelOnExisting(
        self,
        outputFile: OutputFile,
        modelKey: str,
        progressBar,
        tileSize: int,
        tilePadding: int,
        maintainScale: bool,
        device: str,
        operation: Operation = Operation.Sharpen,
        masks: list = None,
    ) -> OutputFile:
        """Run a model on an existing OutputFile, appending the operation"""
        runner = modelRunner.ModelRunner(
            modelKey,
            tileSize,
            tilePadding,
            maintainScale,
            device,
            modelRoot=self.getModelRoot(),
        )
        runner.addObserver(progressBar)
        self.activeOperation = runner
        result = runner.runOnExisting(outputFile, operation, masks=masks)
        runner.removeObserver(progressBar)
        return result

    def runAutoMask(self, file: InputFile, progressBar):
        if self.doDetect:
            device = self.gpuInfo.getPreferredDevice()
            generateMasksOp = generate_masks.GenerateMasks(device)
            generateMasksOp.addObserver(progressBar)
            self.activeOperation = generateMasksOp
            success = generateMasksOp.run(file)
            generateMasksOp.removeObserver(progressBar)

    def runDetectSubjects(self, file: InputFile, progressBar):
        if self.doDetect:
            device = self.gpuInfo.getPreferredDevice()
            detectSubjects = detect_subjects.GenerateLabels(device)
            detectSubjects.addObserver(progressBar)
            self.activeOperation = detectSubjects
            result = detectSubjects.detect(file)
            detectSubjects.removeObserver(progressBar)
            return result

    def interruptOperation(self):
        if self.activeOperation:
            self.activeOperation.requestInterrupt()

    def rerunOperationChain(
        self,
        compareFile: OutputFile,
        startIndex: int,
        progressCallback=None,
        tileSize: int = 512,
        tilePadding: int = 32,
    ) -> bool:
        """Re-run operations starting from the given index."""
        # Collect the operations that need to be re-run (from startIndex onwards)
        opsToRerun = list(compareFile.operations[startIndex:])

        # Remove these operations from the file
        compareFile.removeOperationsFrom(startIndex)

        # Reset the file path to the state before these operations
        if startIndex == 0:
            # Copy base file to cache and set as current path
            rootPath = os.getcwd() + "/.cache/"
            if not os.path.exists(rootPath):
                os.makedirs(rootPath)
            baseName = os.path.basename(compareFile.baseFile.path)
            base, ext = os.path.splitext(baseName)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            newPath = os.path.join(rootPath, f"{base}_reset_{timestamp}{ext}")
            shutil.copyfile(compareFile.baseFile.path, newPath)
            compareFile.setPath(newPath)
        else:
            # Use reapplyStrength to regenerate from previous operations
            compareFile.reapplyStrength(compareFile.operations[-1])

        # Get preferred device
        device = self.gpuInfo.getPreferredDevice()

        # Re-run each operation
        for op in opsToRerun:
            maintainScale = op.scale is not None and op.scale < 1.0

            runner = modelRunner.ModelRunner(
                op.modelPath,
                tileSize,
                tilePadding,
                maintainScale,
                device,
                modelRoot=self.getModelRoot(),
            )
            if progressCallback:
                runner.addObserver(progressCallback)
            self.activeOperation = runner

            result = runner.runOnExisting(
                compareFile,
                op.operation_type,
                masks=op.masks if op.masks else None,
            )

            if progressCallback:
                runner.removeObserver(progressCallback)

            if result is None:
                logger.error(f"Failed to re-run operation: {op.operation_type}")
                return False

            # Apply the strength from the original operation
            newOp = compareFile.operations[-1]
            if newOp.supportsStrength() and op.strength is not None:
                newOp.strength = op.strength
                compareFile.reapplyStrength(newOp)

        return True

    def getModelRoot(self) -> str:
        return os.path.join("models/")

    def getModels(self, installed=False):
        modelListPath = self.getModelRoot() + MODEL_CONFIG
        try:
            with open(modelListPath, "r") as f:
                models = json.load(f)
            if installed:
                models = {
                    path: model
                    for path, model in models.items()
                    if model.get("installed")
                }
            return models
        except Exception as e:
            return {}

    def storeModels(self, models):
        modelListPath = self.getModelPath() + MODEL_CONFIG
        with open(modelListPath, "w") as f:
            json.dump(models, f, indent=4)

    def fetchFile(self, path):
        modelInstallPath = self.getModelRoot()
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
                modelData["installed"] = False
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
