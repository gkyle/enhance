from functools import partial
import time
from PySide6.QtCore import QObject, Signal, QThreadPool, QEvent
from PySide6.QtWidgets import QWidget, QPushButton, QFrame
from PySide6.QtCore import QThread, QRunnable

from enhance.lib.file import File
from enhance.ui.common import RenderMode


WorkerHistory = []


class WorkerStatus:
    def __init__(self, label, status, scheduleTime, latency=None):
        self.label = label
        self.status = status
        self.scheduleTime = scheduleTime
        self.latency = latency
        if self.label is not None:
            WorkerHistory.append(self)


class AsyncWorker(QRunnable):

    def __init__(self, work, parent=None, label=None):
        super().__init__(parent)
        self.signals = getSignals()
        self.work = work
        self.status = WorkerStatus(label, "scheduled", time.time())

    def run(self):
        if not QThread.currentThread().isInterruptionRequested():
            self.status.status = "running"
            startTime = time.time()
            self.work()
            endTime = time.time()
            self.status.latency = endTime - startTime
            self.status.status = "finished"
        else:
            self.status.status = "interrupted"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Signals(QObject):
    startProgress: Signal = Signal(int, str)
    incrementProgress: Signal = Signal(object, int, int, int, bool, object)

    showFiles: Signal = Signal(bool)
    setRenderMode: Signal = Signal(RenderMode)
    setShowMasks: Signal = Signal(bool)
    selectBaseFile: Signal = Signal(File, bool)
    selectCompareFile: Signal = Signal(File)
    updateIndicator: Signal = Signal(File, int)
    updateGPUStats: Signal = Signal()

    addFileButton: Signal = Signal(QWidget, QPushButton, bool)
    focusFile: Signal = Signal(File)
    updateThumbnail: Signal = Signal(QFrame, QWidget)
    drawFileList: Signal = Signal(File)
    appendFile: Signal = Signal(File)

    removeFile: Signal = Signal(File, QPushButton)
    saveFile: Signal = Signal(File, QPushButton)

    windowResized: Signal = Signal(QEvent)
    windowMoved: Signal = Signal(QEvent)

    changeZoom: Signal = Signal(float)

    taskCompleted: Signal = Signal()


lowpri_threadpool = QThreadPool()
lowpri_threadpool.setMaxThreadCount(1)


def emitLater(emit, *args, priority=0):
    worker = AsyncWorker(partial(emit, *args))
    pool = lowpri_threadpool
    pool.start(worker, priority=priority)


signals = Signals()


# global accessor for shared Signals
def getSignals():
    return signals
