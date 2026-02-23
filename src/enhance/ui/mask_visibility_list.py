from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QCheckBox,
    QLabel,
)
from PySide6.QtCore import Signal
from typing import List

from enhance.lib.file import Mask


class MaskVisibilityList(QFrame):
    """A widget that displays a list of masks with checkboxes to toggle visibility."""

    visibilityChanged = Signal(set)  # Emits the set of visible mask indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.masks: List[Mask] = []
        self.checkboxes: List[QCheckBox] = []
        self.setupUi()

    def setupUi(self):
        self.setFrameShape(QFrame.NoFrame)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

    def setMasks(self, masks: List[Mask]):
        """Update the list of masks displayed."""
        # Clear existing checkboxes
        for checkbox in self.checkboxes:
            self.layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.checkboxes.clear()

        self.masks = masks if masks else []

        # Create checkboxes for each mask
        for idx, mask in enumerate(self.masks):
            checkbox = QCheckBox(mask.uniqueLabel)
            checkbox.setStyleSheet("color: #aaa;")
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self._onCheckboxChanged)
            self.checkboxes.append(checkbox)
            self.layout.addWidget(checkbox)

    def _onCheckboxChanged(self):
        """Handle checkbox state changes."""
        visible = set()
        for idx, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                visible.add(idx)
        self.visibilityChanged.emit(visible)

    def getVisibleIndices(self) -> set:
        """Get the set of currently visible mask indices."""
        visible = set()
        for idx, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                visible.add(idx)
        return visible

    def setAllVisible(self, visible: bool):
        """Set all masks visible or hidden."""
        for checkbox in self.checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(visible)
            checkbox.blockSignals(False)
        self._onCheckboxChanged()
