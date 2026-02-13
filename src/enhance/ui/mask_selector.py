"""
Custom mask selector widget with dropdown menu.
Shows checkable masks with inside/outside selection per mask.
"""
from PySide6.QtWidgets import (
    QToolButton,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QLabel,
    QFrame,
    QVBoxLayout,
    QButtonGroup,
    QApplication,
)
from PySide6.QtCore import Signal, Qt, QPoint, QTimer

from typing import List, Tuple
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
        self.checkbox.stateChanged.connect(self._onCheckboxChanged)
        layout.addWidget(self.checkbox)
        
        layout.addStretch()
        
        # Clickable label that toggles between inside/outside
        self.modeLabel = ClickableLabel("inside")
        self.modeLabel.setFixedWidth(70)
        self.modeLabel.setAlignment(Qt.AlignCenter)
        self.modeLabel.setCursor(Qt.PointingHandCursor)
        self.modeLabel.clicked.connect(self._toggleMode)
        self._applyInsideStyle()
        layout.addWidget(self.modeLabel)
    
    def _toggleMode(self):
        """Toggle between inside and outside."""
        if not self.checkbox.isChecked():
            # Auto-check the checkbox when clicking mode
            self.checkbox.setChecked(True)
        self._inverted = not self._inverted
        self._applyModeStyle()
        self._onChanged()
    
    def _onCheckboxChanged(self, state):
        self._applyModeStyle()
        self._onChanged()
    
    def _applyModeStyle(self):
        if self._inverted:
            self._applyOutsideStyle()
        else:
            self._applyInsideStyle()
    
    def _applyInsideStyle(self):
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
    
    def _applyOutsideStyle(self):
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
    
    def _onChanged(self):
        self.changed.emit()
    
    def isSelected(self) -> bool:
        return self.checkbox.isChecked()
    
    def setSelected(self, selected: bool):
        self.checkbox.setChecked(selected)
        self._applyModeStyle()
    
    def isInverted(self) -> bool:
        return self._inverted
    
    def setInverted(self, inverted: bool):
        self._inverted = inverted
        self._applyModeStyle()


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
        
        self.maskWidgets: List[MaskItemWidget] = []
        self._initialSelection = []
    
    def showEvent(self, event):
        """Remember selection state when popup opens."""
        super().showEvent(event)
        self._initialSelection = self._getSelectionKey()
    
    def hideEvent(self, event):
        """Emit signal when popup closes if selection changed."""
        super().hideEvent(event)
        currentSelection = self._getSelectionKey()
        if currentSelection != self._initialSelection:
            self.selectionChanged.emit(self.getSelection())
        self.closed.emit()
    
    def _getSelectionKey(self) -> tuple:
        """Get a hashable key representing the current selection state."""
        return tuple((w.mask.uniqueLabel, w.isSelected(), w.isInverted()) for w in self.maskWidgets)
    
    def setMasks(self, masks: List[Mask], selectedMasks: List[Mask] = None):
        """Set the available masks."""
        # Clear existing widgets
        for widget in self.maskWidgets:
            widget.deleteLater()
        self.maskWidgets.clear()
        
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Build a dict of selected mask labels to their inverted state
        selectedMaskInfo = {m.uniqueLabel: m.inverted for m in (selectedMasks or [])}
        
        for mask in masks:
            itemWidget = MaskItemWidget(mask)
            
            # Pre-select if in selectedMasks and set inverted state
            if mask.uniqueLabel in selectedMaskInfo:
                itemWidget.setSelected(True)
                itemWidget.setInverted(selectedMaskInfo[mask.uniqueLabel])
            
            self.layout.addWidget(itemWidget)
            self.maskWidgets.append(itemWidget)
        
        self.adjustSize()
    
    def getSelection(self) -> List[Mask]:
        """Get the current selection with per-mask inverted property set."""
        selectedMasks = []
        
        for widget in self.maskWidgets:
            if widget.isSelected():
                # Set the inverted property on the mask
                widget.mask.inverted = widget.isInverted()
                selectedMasks.append(widget.mask)
        
        return selectedMasks


class MaskSelectorButton(QToolButton):
    """
    A button that opens a dropdown menu for selecting masks.
    Each mask can be toggled and set to inside/outside mode.
    """
    
    selectionChanged = Signal(list)  # List of Mask objects with inverted property set
    
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
        
        self.clicked.connect(self._showPopup)
    
    def _showPopup(self):
        """Show the popup with mask options."""
        if not self.popup or not self.masks:
            return
        
        # Position popup below the button
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.move(pos)
        self.popup.show()
    
    def setMasks(self, masks: List[Mask], selectedMasks: List[Mask] = None):
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
            self.popup.selectionChanged.connect(self._onPopupSelectionChanged)
            self.popup.closed.connect(self._updateButtonText)
        
        self.popup.setMasks(masks, selectedMasks)
        self._updateButtonText()
    
    def _onPopupSelectionChanged(self, selectedMasks: list):
        """Handle selection changes from the popup."""
        self.selectionChanged.emit(selectedMasks)
    
    def _updateButtonText(self):
        """Update the button text to reflect current selection."""
        if not self.popup:
            return
        
        selected = [w for w in self.popup.maskWidgets if w.isSelected()]
        
        if not selected:
            self.setText("Masks: None")
        elif len(selected) == 1:
            mode = "outside" if selected[0].isInverted() else "inside"
            self.setText(f"Mask: {selected[0].mask.uniqueLabel} ({mode})")
        else:
            # Check if all have same mode
            modes = set(w.isInverted() for w in selected)
            if len(modes) == 1:
                mode = "outside" if selected[0].isInverted() else "inside"
                self.setText(f"Masks: {len(selected)} selected ({mode})")
            else:
                self.setText(f"Masks: {len(selected)} selected (mixed)")
    
    def getSelection(self) -> List[Mask]:
        """Get the current selection."""
        if self.popup:
            return self.popup.getSelection()
        return []
    
    def setSelection(self, selectedMasks: List[Mask]):
        """Set the current selection programmatically."""
        if self.popup:
            # Build a dict of selected mask labels to their inverted state
            selectedMaskInfo = {m.uniqueLabel: m.inverted for m in selectedMasks}
            
            for widget in self.popup.maskWidgets:
                if widget.mask.uniqueLabel in selectedMaskInfo:
                    widget.setSelected(True)
                    widget.setInverted(selectedMaskInfo[widget.mask.uniqueLabel])
                else:
                    widget.setSelected(False)
            
            self._updateButtonText()

