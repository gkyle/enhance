"""
Mask selector widget with dropdown menu.
Shows checkable masks with inside/outside selection per mask.
"""

from PySide6.QtWidgets import (
    QToolButton,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QFrame,
    QVBoxLayout,
)
from PySide6.QtCore import Signal, Qt, QPoint

import copy
from typing import List
from enhance.lib.file import Mask


class ClickableLabel(QLabel):
    """A QLabel that emits a signal when clicked."""
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()  # Accept the event to prevent it from propagating


class MaskItemWidget(QWidget):
    """Widget for a single mask item in the dropdown menu."""

    changed = Signal()  # Emitted when checkbox or mode changes

    def __init__(self, mask: Mask, parent=None):
        super().__init__(parent)
        self.mask = mask
        self._inverted = False
        self.setupUi()

    def setupUi(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Checkbox for selecting the mask
        self.checkbox = QCheckBox(self.mask.uniqueLabel)
        self.checkbox.setStyleSheet("color: #ddd;")
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        layout.addStretch()

        # Clickable label that toggles between inside/outside
        self.modeLabel = ClickableLabel("inside")
        self.modeLabel.setFixedWidth(70)
        self.modeLabel.setAlignment(Qt.AlignCenter)
        self.modeLabel.setCursor(Qt.PointingHandCursor)
        self.modeLabel.clicked.connect(self._toggle_mode)
        self._apply_inside_style()
        layout.addWidget(self.modeLabel)

    def _toggle_mode(self):
        """Toggle between inside and outside."""
        if not self.checkbox.isChecked():
            # Auto-check the checkbox when clicking mode
            self.checkbox.setChecked(True)
        self._inverted = not self._inverted
        self._apply_mode_style()
        self._on_changed()

    def _on_checkbox_changed(self, state):
        self._apply_mode_style()
        self._on_changed()

    def _apply_mode_style(self):
        if self._inverted:
            self._apply_outside_style()
        else:
            self._apply_inside_style()

    def _apply_inside_style(self):
        self.modeLabel.setText("inside")
        if self.checkbox.isChecked():
            self.modeLabel.setStyleSheet("""
                QLabel {
                    color: #fff;
                    padding: 2px 6px;
                    border: 1px solid #5a9f5a;
                    border-radius: 3px;
                    background-color: #4a8f4a;
                }
            """)
        else:
            self.modeLabel.setStyleSheet("""
                QLabel {
                    color: #888;
                    padding: 2px 6px;
                    border: 1px solid #555;
                    border-radius: 3px;
                    background-color: #3a3a3a;
                }
            """)

    def _apply_outside_style(self):
        self.modeLabel.setText("outside")
        if self.checkbox.isChecked():
            self.modeLabel.setStyleSheet("""
                QLabel {
                    color: #fff;
                    padding: 2px 6px;
                    border: 1px solid #5a7fb5;
                    border-radius: 3px;
                    background-color: #4a6fa5;
                }
            """)
        else:
            self.modeLabel.setStyleSheet("""
                QLabel {
                    color: #888;
                    padding: 2px 6px;
                    border: 1px solid #555;
                    border-radius: 3px;
                    background-color: #3a3a3a;
                }
            """)

    def _on_changed(self):
        self.changed.emit()

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    def set_selected(self, selected: bool):
        self.checkbox.setChecked(selected)
        self._apply_mode_style()

    def is_inverted(self) -> bool:
        return self._inverted

    def set_inverted(self, inverted: bool):
        self._inverted = inverted
        self._apply_mode_style()


class MaskPopupFrame(QFrame):
    """A popup frame containing mask selection widgets."""

    selectionChanged = Signal(list)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            MaskPopupFrame {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)

        self.mask_widgets: List[MaskItemWidget] = []
        self._initialSelection = []

    def showEvent(self, event):
        """Remember selection state when popup opens."""
        super().showEvent(event)
        self._initialSelection = self._get_selection_key()

    def hideEvent(self, event):
        """Emit signal when popup closes if selection changed."""
        super().hideEvent(event)
        current_selection = self._get_selection_key()
        if current_selection != self._initialSelection:
            self.selectionChanged.emit(self.get_selection())
        self.closed.emit()

    def _get_selection_key(self) -> tuple:
        """Get a hashable key representing the current selection state."""
        return tuple(
            (w.mask.uniqueLabel, w.is_selected(), w.is_inverted())
            for w in self.mask_widgets
        )

    def set_masks(self, masks: List[Mask], selected_masks: List[Mask] = None):
        """Set the available masks."""
        # Clear existing widgets
        for widget in self.mask_widgets:
            widget.deleteLater()
        self.mask_widgets.clear()

        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build a dict of selected mask labels to their inverted state
        selected_mask_info = {m.uniqueLabel: m.inverted for m in (selected_masks or [])}

        for mask in masks:
            item_widget = MaskItemWidget(mask)

            # Pre-select if in selected_masks and set inverted state
            if mask.uniqueLabel in selected_mask_info:
                item_widget.set_selected(True)
                item_widget.set_inverted(selected_mask_info[mask.uniqueLabel])

            self.layout.addWidget(item_widget)
            self.mask_widgets.append(item_widget)

        self.adjustSize()

    def get_selection(self) -> List[Mask]:
        """Get the current selection with per-mask inverted property set."""
        selected_masks = []

        for widget in self.mask_widgets:
            if widget.is_selected():
                mask_copy = copy.copy(widget.mask)
                mask_copy.inverted = widget.is_inverted()
                selected_masks.append(mask_copy)

        return selected_masks


class MaskSelectorButton(QToolButton):
    """
    A button that opens a dropdown menu for selecting masks.
    Each mask can be toggled and set to inside/outside mode.
    """

    selectionChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.masks: List[Mask] = []
        self.popup: MaskPopupFrame = None

        self.setText("Masks: None")
        self.setStyleSheet("""
            QToolButton {
                background-color: #3d3d3d;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 12px;
                text-align: left;
            }
            QToolButton:hover {
                background-color: #4d4d4d;
            }
        """)

        self.clicked.connect(self._show_popup)

    def _show_popup(self):
        """Show the popup with mask options."""
        if not self.popup or not self.masks:
            return

        # Position popup below the button
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.move(pos)
        self.popup.show()

    def set_masks(self, masks: List[Mask], selected_masks: List[Mask] = None):
        """Set the available masks and optionally pre-select some."""
        self.masks = masks

        if not masks:
            self.setText("Masks: None available")
            self.setEnabled(False)
            if self.popup:
                self.popup.hide()
            return

        self.setEnabled(True)

        # Create popup if needed
        if self.popup is None:
            self.popup = MaskPopupFrame()
            self.popup.selectionChanged.connect(self._on_popup_selection_changed)
            self.popup.closed.connect(self._update_button_text)

        self.popup.set_masks(masks, selected_masks)
        self._update_button_text()

    def _on_popup_selection_changed(self, selected_masks: list):
        """Handle selection changes from the popup."""
        self.selectionChanged.emit(selected_masks)

    def _update_button_text(self):
        """Update the button text to reflect current selection."""
        if not self.popup:
            return

        selected = [w for w in self.popup.mask_widgets if w.is_selected()]

        if not selected:
            self.setText("Masks: None")
        elif len(selected) == 1:
            mode = "outside" if selected[0].is_inverted() else "inside"
            self.setText(f"Mask: {selected[0].mask.uniqueLabel} ({mode})")
        else:
            # Check if all have same mode
            modes = set(w.is_inverted() for w in selected)
            if len(modes) == 1:
                mode = "outside" if selected[0].is_inverted() else "inside"
                self.setText(f"Masks: {len(selected)} selected ({mode})")
            else:
                self.setText(f"Masks: {len(selected)} selected (mixed)")

    def get_selection(self) -> List[Mask]:
        """Get the current selection."""
        if self.popup:
            return self.popup.get_selection()
        return []

    def set_selection(self, selected_masks: List[Mask]):
        """Set the current selection programmatically."""
        if self.popup:
            # Build a dict of selected mask labels to their inverted state
            selected_mask_info = {m.uniqueLabel: m.inverted for m in selected_masks}

            for widget in self.popup.mask_widgets:
                if widget.mask.uniqueLabel in selected_mask_info:
                    widget.set_selected(True)
                    widget.set_inverted(selected_mask_info[widget.mask.uniqueLabel])
                else:
                    widget.set_selected(False)

            self._update_button_text()
