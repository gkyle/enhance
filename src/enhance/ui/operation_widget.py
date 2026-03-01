from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics

from enhance.lib.file import AppliedOperation, Mask
from enhance.ui.mask_selector import MaskSelectorButton
from typing import List


class OperationWidget(QFrame):
    """A widget that displays a single operation with its controls."""

    strengthChanged = Signal(AppliedOperation, float)
    masksChanged = Signal(AppliedOperation, list)

    def __init__(self, operation: AppliedOperation, available_masks: List[Mask] = None, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.available_masks = available_masks if available_masks else []
        self.mask_selector: MaskSelectorButton = None
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
        name_label = QLabel(self._get_operation_display_name())
        name_label.setStyleSheet("font-weight: bold; color: #fff;")
        layout.addWidget(name_label)

        # Model name (if applicable)
        if self.operation.model:
            model_frame = QFrame()
            model_frame.setFrameShape(QFrame.NoFrame)
            model_layout = QHBoxLayout(model_frame)
            model_layout.setContentsMargins(0, 0, 0, 0)
            model_layout.setSpacing(4)

            model_label = QLabel()
            metrics = QFontMetrics(model_label.font())
            elided = metrics.elidedText(
                self.operation.model, Qt.TextElideMode.ElideMiddle, 200
            )
            model_label.setText(elided)
            model_label.setToolTip(self.operation.model)
            model_label.setStyleSheet("color: #9a9996;")
            model_layout.addWidget(model_label)
            model_layout.addStretch()

            layout.addWidget(model_frame)

        # Strength slider (if applicable)
        if self.operation.supportsStrength():
            strength_frame = QFrame()
            strength_frame.setFrameShape(QFrame.NoFrame)
            strength_layout = QVBoxLayout(strength_frame)
            strength_layout.setContentsMargins(0, 4, 0, 0)
            strength_layout.setSpacing(2)

            strength_header_layout = QHBoxLayout()
            strength_header_layout.setContentsMargins(0, 0, 0, 0)

            strength_title_label = QLabel("Strength:")
            strength_title_label.setStyleSheet("color: #aaa;")
            strength_header_layout.addWidget(strength_title_label)

            strength_pct = int((self.operation.strength if self.operation.strength is not None else 1.0) * 100)
            self.strength_value_label = QLabel(f"{strength_pct}%")
            self.strength_value_label.setStyleSheet("color: #aaa;")
            self.strength_value_label.setMinimumWidth(35)
            strength_header_layout.addWidget(self.strength_value_label)
            strength_header_layout.addStretch()

            strength_layout.addLayout(strength_header_layout)

            slider_frame = QFrame()
            slider_frame.setFrameShape(QFrame.NoFrame)
            slider_layout = QHBoxLayout(slider_frame)
            slider_layout.setContentsMargins(0, 0, 0, 0)

            self.strength_slider = QSlider(Qt.Horizontal)
            self.strength_slider.setMinimum(0)
            self.strength_slider.setMaximum(100)
            self.strength_slider.setValue(strength_pct)
            self.strength_slider.setTickPosition(QSlider.TicksBothSides)
            self.strength_slider.setTickInterval(10)
            self.strength_slider.valueChanged.connect(self._on_strength_changed)
            slider_layout.addWidget(self.strength_slider)

            strength_layout.addWidget(slider_frame)
            layout.addWidget(strength_frame)

        # Scale display (if applicable)
        if self.operation.scale is not None and self.operation.scale < 1.0:
            scale_frame = QFrame()
            scale_frame.setFrameShape(QFrame.NoFrame)
            scale_layout = QHBoxLayout(scale_frame)
            scale_layout.setContentsMargins(0, 4, 0, 0)
            scale_layout.setSpacing(4)

            scale_title_label = QLabel("Downscale:")
            scale_title_label.setStyleSheet("color: #aaa;")
            scale_layout.addWidget(scale_title_label)

            scale_value = f"{int(1 / self.operation.scale)}X"
            scale_value_label = QLabel(scale_value)
            scale_value_label.setStyleSheet("color: #9a9996;")
            scale_layout.addWidget(scale_value_label)
            scale_layout.addStretch()

            layout.addWidget(scale_frame)

        # Mask selector button (always show, even if no masks yet)
        self._create_mask_selector(layout)

    def _create_mask_selector(self, layout: QVBoxLayout):
        """Create the mask selector button."""
        masks_frame = QFrame()
        masks_frame.setFrameShape(QFrame.NoFrame)
        masks_layout = QHBoxLayout(masks_frame)
        masks_layout.setContentsMargins(0, 4, 0, 0)
        masks_layout.setSpacing(4)

        self.mask_selector = MaskSelectorButton()
        self.mask_selector.set_masks(
            self.available_masks, selected_masks=self.operation.masks
        )
        self.mask_selector.selectionChanged.connect(self._on_mask_selection_changed)
        masks_layout.addWidget(self.mask_selector)
        masks_layout.addStretch()

        layout.addWidget(masks_frame)
        self.masks_frame = masks_frame

    def _get_operation_display_name(self) -> str:
        """Get a human-readable name for the operation."""
        if self.operation.operation_type:
            return self.operation.operation_type.value
        return "Unknown"

    def _on_strength_changed(self, value: int):
        """Handle strength slider value changes."""
        strength = value / 100.0
        self.strength_value_label.setText(f"{value}%")
        self.strengthChanged.emit(self.operation, strength)

    def _on_mask_selection_changed(self, selected_masks: list):
        """Handle mask selection changes from the mask selector."""
        self.masksChanged.emit(self.operation, selected_masks)

    def get_strength(self) -> float:
        """Get the current strength value."""
        if hasattr(self, 'strength_slider'):
            return self.strength_slider.value() / 100.0
        return self.operation.strength or 1.0

    def get_selected_masks(self) -> List[Mask]:
        """Get the currently selected masks."""
        if self.mask_selector:
            return self.mask_selector.get_selection()
        return []

    def update_available_masks(self, new_masks: List[Mask]):
        """Update the available masks in the mask selector."""
        if len(new_masks) == len(self.available_masks):
            return

        self.available_masks = new_masks

        if self.mask_selector:
            self.mask_selector.set_masks(new_masks, selected_masks=self.operation.masks)
