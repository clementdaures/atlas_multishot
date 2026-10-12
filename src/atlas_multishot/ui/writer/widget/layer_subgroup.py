# -*- coding: utf-8 -*-
"""Collapsible SET / CHR sub-group widget for the Atlas USD Writer UI

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# pyside modules
try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

# atlas modules
import atlas_manager.plugins.lighting.ui.writer.widget.layer_row as layer_row

# endregion

# ==========

# region Layer SubGroup Widget

class LayerSubGroup(QtWidgets.QWidget):
    """Collapsible sub-group (SET or CHR) containing a list of LayerRows.

    Args:
        title (str): Group title, 'SET' or 'CHR'.
        layers (list[str]): Layer names to create a row for.
        start (int): Default start frame of each row.
        end (int): Default end frame of each row.
        parent (QWidget, optional): Parent widget.
    """

    def __init__(self, title: str, layers: list[str], start: int, end: int, parent=None):
        super().__init__(parent)
        self._title = title
        self._expanded = True
        self._layer_rows: list[layer_row.LayerRow] = []

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("background-color: #2c2c2c; border-radius: 2px;")
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(4, 3, 4, 3)

        self._toggle_btn = QtWidgets.QPushButton(f"▼  {title}")
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "font-size: 8pt; color: #aaa; text-align: left; }"
        )
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn, 1)
        outer.addWidget(header_widget)

        self._content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(self._content)
        content_layout.setContentsMargins(16, 2, 0, 2)
        content_layout.setSpacing(2)

        if layers:
            for layer in layers:
                row = layer_row.LayerRow(layer, start, end, 1)
                self._layer_rows.append(row)
                content_layout.addWidget(row)
        else:
            content_layout.addWidget(QtWidgets.QLabel("(none)"))

        outer.addWidget(self._content)

    def _toggle(self) -> None:
        """Expand or collapse the group."""
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._toggle_btn.setText(f"{'▼' if self._expanded else '▶'}  {self._title}")

    def layer_configs(self) -> list[tuple[str, dict]]:
        """Return the frame settings of every layer in this group.

        Returns:
            list[tuple[str, dict]]: (render layer, frame config) pairs.
        """
        return [(row.renderlayer, row.frame_config()) for row in self._layer_rows]

# endregion
