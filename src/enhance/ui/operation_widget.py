from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt, Signal

from enhance.lib.file import AppliedOperation, Mask
from enhance.ui.mask_selector import MaskSelectorButton
from typing import List


class OperationWidget(QFrame):
    """A widget that displays a single operation with its controls."""

    strengthChanged = Signal(AppliedOperation, float)
    masksChanged = Signal(AppliedOperation, list)

    def __init__(self, operation: AppliedOperation, availableMasks: List[Mask] = None, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.availableMasks = availableMasks if availableMasks else []
        self.maskSelector: MaskSelectorButton = None
        self.setupUi()

    def setupUi(self):
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            OperationWidget {
                border: 1px solid rgb(92, 92, 92);
                border-radius: 4px;
                margin: 2px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Operation name header
        nameLabel = QLabel(self._getOperationDisplayName())
        nameLabel.setStyleSheet("font-weight: bold; color: #fff;")
        layout.addWidget(nameLabel)

        # Model name (if applicable)
        if self.operation.model:
            modelFrame = QFrame()
            modelFrame.setFrameShape(QFrame.NoFrame)
            modelLayout = QHBoxLayout(modelFrame)
            modelLayout.setContentsMargins(12, 0, 0, 0)
            modelLayout.setSpacing(4)

            modelLabel = QLabel(self.operation.model)
            modelLabel.setStyleSheet("color: #9a9996;")
            modelLayout.addWidget(modelLabel)
            modelLayout.addStretch()

            layout.addWidget(modelFrame)

        # Strength slider (if applicable)
        if self.operation.supportsStrength():
            strengthFrame = QFrame()
            strengthFrame.setFrameShape(QFrame.NoFrame)
            strengthLayout = QVBoxLayout(strengthFrame)
            strengthLayout.setContentsMargins(0, 4, 0, 0)
            strengthLayout.setSpacing(2)

            strengthHeaderLayout = QHBoxLayout()
            strengthHeaderLayout.setContentsMargins(0, 0, 0, 0)

            strengthTitleLabel = QLabel("Strength:")
            strengthTitleLabel.setStyleSheet("color: #aaa;")
            strengthHeaderLayout.addWidget(strengthTitleLabel)

            self.strengthValueLabel = QLabel(f"{int((self.operation.strength or 1.0) * 100)}%")
            self.strengthValueLabel.setStyleSheet("color: #aaa;")
            self.strengthValueLabel.setMinimumWidth(35)
            strengthHeaderLayout.addWidget(self.strengthValueLabel)
            strengthHeaderLayout.addStretch()

            strengthLayout.addLayout(strengthHeaderLayout)

            sliderFrame = QFrame()
            sliderFrame.setFrameShape(QFrame.NoFrame)
            sliderLayout = QHBoxLayout(sliderFrame)
            sliderLayout.setContentsMargins(12, 0, 0, 0)

            self.strengthSlider = QSlider(Qt.Horizontal)
            self.strengthSlider.setMinimum(0)
            self.strengthSlider.setMaximum(100)
            self.strengthSlider.setValue(int((self.operation.strength or 1.0) * 100))
            self.strengthSlider.setTickPosition(QSlider.TicksBothSides)
            self.strengthSlider.setTickInterval(10)
            self.strengthSlider.valueChanged.connect(self._onStrengthChanged)
            sliderLayout.addWidget(self.strengthSlider)

            strengthLayout.addWidget(sliderFrame)
            layout.addWidget(strengthFrame)

        # Scale display (if applicable)
        if self.operation.scale is not None and self.operation.scale < 1.0:
            scaleFrame = QFrame()
            scaleFrame.setFrameShape(QFrame.NoFrame)
            scaleLayout = QHBoxLayout(scaleFrame)
            scaleLayout.setContentsMargins(0, 4, 0, 0)
            scaleLayout.setSpacing(4)

            scaleTitleLabel = QLabel("Downscale:")
            scaleTitleLabel.setStyleSheet("color: #aaa;")
            scaleLayout.addWidget(scaleTitleLabel)

            scaleValue = f"{int(1 / self.operation.scale)}X"
            scaleValueLabel = QLabel(scaleValue)
            scaleValueLabel.setStyleSheet("color: #9a9996;")
            scaleLayout.addWidget(scaleValueLabel)
            scaleLayout.addStretch()

            layout.addWidget(scaleFrame)

        # Mask selector button (always show, even if no masks yet)
        self._createMaskSelector(layout)

    def _createMaskSelector(self, layout: QVBoxLayout):
        """Create the mask selector button."""
        masksFrame = QFrame()
        masksFrame.setFrameShape(QFrame.NoFrame)
        masksLayout = QHBoxLayout(masksFrame)
        masksLayout.setContentsMargins(0, 4, 0, 0)
        masksLayout.setSpacing(4)

        self.maskSelector = MaskSelectorButton()
        self.maskSelector.setMasks(
            self.availableMasks, selectedMasks=self.operation.masks
        )
        self.maskSelector.selectionChanged.connect(self._onMaskSelectionChanged)
        masksLayout.addWidget(self.maskSelector)
        masksLayout.addStretch()

        layout.addWidget(masksFrame)
        self.masksFrame = masksFrame

    def _getOperationDisplayName(self) -> str:
        """Get a human-readable name for the operation."""
        if self.operation.operation_type:
            return self.operation.operation_type.value
        return "Unknown"

    def _onStrengthChanged(self, value: int):
        """Handle strength slider value changes."""
        strength = value / 100.0
        self.strengthValueLabel.setText(f"{value}%")
        self.strengthChanged.emit(self.operation, strength)

    def _onMaskSelectionChanged(self, selectedMasks: list):
        """Handle mask selection changes from the mask selector."""
        self.masksChanged.emit(self.operation, selectedMasks)

    def getStrength(self) -> float:
        """Get the current strength value."""
        if hasattr(self, 'strengthSlider'):
            return self.strengthSlider.value() / 100.0
        return self.operation.strength or 1.0

    def getSelectedMasks(self) -> List[Mask]:
        """Get the currently selected masks."""
        if self.maskSelector:
            return self.maskSelector.getSelection()
        return []

    def updateAvailableMasks(self, newMasks: List[Mask]):
        """Update the available masks in the mask selector."""
        if len(newMasks) == len(self.availableMasks):
            return

        self.availableMasks = newMasks

        if self.maskSelector:
            self.maskSelector.setMasks(newMasks, selectedMasks=self.operation.masks)
