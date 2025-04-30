
from typing import List
from upscale.lib.file import File
from upscale.ui.signals import Signals, emitLater
from upscale.ui.common import RenderMode

CLEAR = -1


class SelectionManager:
    def __init__(self, signals: Signals):
        self.signals: Signals = signals
        self.renderMode: RenderMode = RenderMode.Single

        self.base: File = None
        self.compare: List[File] = []

        self.signals.selectCompareFile.connect(self.selectCompare)
        self.signals.selectBaseFile.connect(self.selectBase)
        self.signals.setRenderMode.connect(self.setRenderMode)

    def selectBase(self, file):
        if file == self.base:
            return
        if file in self.compare:
            self.compare.remove(file)
        if self.base is not None:
            self.signals.updateIndicator.emit(self.base, CLEAR)

        self.base = file
        self.signals.updateIndicator.emit(file, 0)
        emitLater(self.signals.showFiles.emit)

        if len(self.compare) == 0:
            self.signals.setRenderMode.emit(RenderMode.Single)

    def selectCompare(self, file):
        if file == self.base:
            return
        if file in self.compare:
            self.compare.remove(file)
            self.signals.updateIndicator.emit(file, CLEAR)

        self.compare.insert(0, file)
        if len(self.compare) > 4:
            rmFile = self.compare.pop()
            self.signals.updateIndicator.emit(rmFile, CLEAR)

        for idx, f in enumerate(self.compare):
            self.signals.updateIndicator.emit(f, idx+1)
        emitLater(self.signals.showFiles.emit)

        if self.renderMode == RenderMode.Single:
            self.signals.setRenderMode.emit(RenderMode.Split)

    def removeFile(self, file):
        if file == self.base:
            self.base = None
            self.signals.updateIndicator.emit(file, CLEAR)
        elif file in self.compare:
            self.compare.remove(file)
            self.signals.updateIndicator.emit(file, CLEAR)

        emitLater(self.signals.showFiles.emit)

    def clear(self):
        if self.base is not None:
            self.signals.updateIndicator.emit(self.base, CLEAR)
            self.base = None

        for file in self.compare:
            self.signals.updateIndicator.emit(file, CLEAR)
        self.compare.clear()

        emitLater(self.signals.showFiles.emit)

    def getBaseFile(self) -> File:
        return self.base

    def getBaseFilename(self) -> str:
        if self.base is None:
            return None
        return self.base.basename

    def getCompareFile(self, idx) -> File:
        if idx >= len(self.compare):
            return None
        return self.compare[idx]

    def getCompareFilename(self, idx) -> str:
        if idx >= len(self.compare):
            return ""
        return self.compare[idx].basename

    def setRenderMode(self, mode: RenderMode):
        self.renderMode = mode
