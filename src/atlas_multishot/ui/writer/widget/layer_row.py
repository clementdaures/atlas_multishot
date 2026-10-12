# -*- coding: utf-8 -*-
"""Per-layer frame range row widget for the Atlas USD Writer UI

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# pyside modules
try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore

# dcc import
import hou

# endregion

# ==========

# region Layer Row Widget

class LayerRow(QtWidgets.QWidget):
    """Row widget holding the frame range of one render layer.

    Layout: FG: [ 1001 ] - [ 1100 ] - [ 1 ]   [ ] single

    Args:
        renderlayer (str): Render layer name, e.g. 'BG'.
        start (int): Default start frame.
        end (int): Default end frame.
        step (int): Default frame step.
        parent (QWidget, optional): Parent widget.
    """

    def __init__(self, renderlayer: str, start: int, end: int, step: int, parent=None):
        super().__init__(parent)
        self._renderlayer = renderlayer

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        label = QtWidgets.QLabel(f"{renderlayer}:")
        label.setMinimumWidth(60)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self._start = QtWidgets.QLineEdit(str(start))
        self._start.setFixedWidth(55)
        self._start.setToolTip("Start frame")

        self._end = QtWidgets.QLineEdit(str(end))
        self._end.setFixedWidth(55)
        self._end.setToolTip("End frame")

        self._step = QtWidgets.QLineEdit(str(step))
        self._step.setFixedWidth(40)
        self._step.setToolTip("Frame step")

        layout.addWidget(self._start)
        layout.addWidget(QtWidgets.QLabel("-"))
        layout.addWidget(self._end)
        layout.addWidget(QtWidgets.QLabel("-"))
        layout.addWidget(self._step)

        self._single_cb = QtWidgets.QCheckBox("single")
        self._single_cb.setToolTip("Render current frame only (overrides range)")
        self._single_cb.stateChanged.connect(self._on_single_toggled)
        layout.addWidget(self._single_cb)

        layout.addStretch()

    def _on_single_toggled(self, state: int) -> None:
        """Enable the range fields only when the single frame option is unchecked.

        Args:
            state (int): Check state of the single checkbox.
        """
        enabled = (state == QtCore.Qt.Unchecked)
        self._start.setEnabled(enabled)
        self._end.setEnabled(enabled)
        self._step.setEnabled(enabled)

    @property
    def renderlayer(self) -> str:
        """str: Render layer name of this row."""
        return self._renderlayer

    def frame_config(self) -> dict:
        """Return the frame settings entered in this row.

        Invalid entries fall back to the timeline range, or to a step of 1.

        Returns:
            dict: Frame settings with the keys 'single' (bool), 'start',
                'end' and 'step'.
        """
        single = self._single_cb.isChecked()
        timeline_start, timeline_end = hou.playbar.frameRange()
        try:
            start = int(self._start.text())
        except ValueError:
            start = int(timeline_start)
        try:
            end = int(self._end.text())
        except ValueError:
            end = int(timeline_end)
        try:
            step = int(self._step.text())
        except ValueError:
            step = 1
        return {"single": single, "start": start, "end": end, "step": step}

# endregion
