# -*- coding: utf-8 -*-
"""Per-shot collapsible panel widget for the Atlas USD Writer UI

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
import atlas_manager.plugins.lighting.ui.writer.widget.layer_subgroup as layer_subgroup

# endregion

# ==========

# region Shot Panel Widget

class ShotPanel(QtWidgets.QWidget):
    """Collapsible panel for one shot, containing SET and CHR sub-groups.

    A master checkbox enables or disables the USD writing of the shot.

    Args:
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
        set_layers (list[str]): Layer names of the SET_LYR network.
        chr_layers (list[str]): Layer names of the CHR_LYR network.
        start (int): Default start frame of each layer.
        end (int): Default end frame of each layer.
        parent (QWidget, optional): Parent widget.
    """

    def __init__(
        self,
        shot_id: str,
        set_layers: list[str],
        chr_layers: list[str],
        start: int,
        end: int,
        parent=None,
    ):
        super().__init__(parent)
        self._shot_id  = shot_id
        self._expanded = True
        self._sub_groups: list[layer_subgroup.LayerSubGroup] = []

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 4)
        outer.setSpacing(0)

        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("background-color: #3a3a3a; border-radius: 3px;")
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(6, 4, 6, 4)
        header_layout.setSpacing(8)

        self._master_cb = QtWidgets.QCheckBox()
        self._master_cb.setChecked(True)
        self._master_cb.setToolTip("Enable / disable USD writing for this shot")
        header_layout.addWidget(self._master_cb)

        self._toggle_btn = QtWidgets.QPushButton(f"▼  {shot_id}")
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "font-weight: bold; font-size: 9pt; text-align: left; }"
        )
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn, 1)
        outer.addWidget(header_widget)

        self._content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(self._content)
        content_layout.setContentsMargins(12, 4, 4, 4)
        content_layout.setSpacing(4)

        for title, layers in [("SET", set_layers), ("CHR", chr_layers)]:
            sub = layer_subgroup.LayerSubGroup(title, layers, start, end)
            self._sub_groups.append(sub)
            content_layout.addWidget(sub)

        outer.addWidget(self._content)

    def _toggle(self) -> None:
        """Expand or collapse the panel."""
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._toggle_btn.setText(f"{'▼' if self._expanded else '▶'}  {self._shot_id}")

    @property
    def shot_id(self) -> str:
        """str: Shot identifier of this panel."""
        return self._shot_id

    def is_enabled(self) -> bool:
        """Check whether USD writing is enabled for this shot.

        Returns:
            bool: State of the master checkbox.
        """
        return self._master_cb.isChecked()

    def layer_configs(self) -> list[tuple[str, dict]]:
        """Return the frame settings of every layer of this shot.

        Returns:
            list[tuple[str, dict]]: (render layer, frame config) pairs from
                the SET and CHR sub-groups.
        """
        configs = []
        for sub in self._sub_groups:
            configs.extend(sub.layer_configs())
        return configs

# endregion
