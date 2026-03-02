from tqdm import tqdm
from PySide6.QtWidgets import QProgressBar, QLabel

from enhance.ui.signals import getSignals


class ProgressBarUpdater(tqdm):
    def __init__(self, qpbar: QProgressBar, qlabel: QLabel, *args, suppressStdout=True, **kwargs):
        tqdm.__init__(self, *args, **kwargs)
        self.qpbar = qpbar
        self.qlabel = qlabel
        self.suppressStdout = suppressStdout
        self.signals = getSignals()

        self.total = None
        if 'total' in kwargs:
            self.total = kwargs['total']
        self.desc = None
        if 'desc' in kwargs:
            self.desc = kwargs['desc']
            self.qlabel.setText(self.desc)

    def set_progress(self, count, total):
        if not total or total == 0:
            return
        self.total = total
        self.n = count
        self.qlabel.setText(self.desc)
        self.qpbar.setValue(count / total * 100)
        f = self.format_meter(count, total, self._time() - self.start_t,
                              bar_format="{n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]")
        self.qpbar.setFormat(f"{f}")

    def tick(self, *args):
        self.signals.incrementProgress.emit(self, *args)
