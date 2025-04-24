from functools import partial
from PySide6.QtCore import QObject, Signal, QThreadPool, QEvent
from PySide6.QtWidgets import QWidget, QPushButton, QFrame
from PySide6.QtCore import QThread, QRunnable

from upscale.lib.file import File
from upscale.ui.common import RenderMode


class AsyncWorker(QRunnable):
    def __init__(self, work, parent=None):
        super().__init__(parent)
        self.signals = getSignals()
        self.work = work

    def run(self):
        if not QThread.currentThread().isInterruptionRequested():
            self.work()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Signals(QObject):
    startProgress: Signal = Signal(int, str)
    incrementProgress: Signal = Signal(object, int, int, int, bool, object)

    showFiles: Signal = Signal()
    setRenderMode: Signal = Signal(RenderMode)
    selectBaseFile: Signal = Signal(File)
    selectCompareFile: Signal = Signal(File)
    updateIndicator: Signal = Signal(File, int)
    updateGPUStats: Signal = Signal()
    updateFile: Signal = Signal(File)
    updateFileButton: Signal = Signal(File)

    addFileButton: Signal = Signal(QWidget, QPushButton, bool)
    focusFile: Signal = Signal(File)
    updateThumbnails: Signal = Signal(QWidget)
    updateThumbnail: Signal = Signal(QFrame, QWidget)
    drawFileList: Signal = Signal(File)
    appendFile: Signal = Signal(File)

    removeFile: Signal = Signal(File, QPushButton)
    saveFile: Signal = Signal(File, QPushButton)

    windowResized: Signal = Signal(QEvent)
    windowMoved: Signal = Signal(QEvent)

    changeZoom: Signal = Signal(float)


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
