# -*- coding: utf-8 -*-
"""Atlas select shot UI class

This module provides the UI for `Select Shot` Lighting, which allows the
currently logged-in artist to pick the active shot among the shots assigned
to them.

When a shot is confirmed:
    - the bypass state and colour of the /stage/shot{XXX} nodes are updated
    - /stage/shot_asb filepath1 is updated
    - the shot and shot_index parameters of /stage/LIGHTING_CTL are updated
    - the Houdini timeline is set to the frame range of the shot

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import os

# pyside modules
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

# dcc import
import hou

# atlas modules
from atlas_multishot.core.utils.parse_sequence import extract_seq_shot
from atlas_multishot.core.utils.scan_shot import discover_shots, shot_exists_on_disk
from atlas_multishot.core.utils.user_db import get_current_artist
import atlas_multishot.core.assignment_manager as assignment_manager
import atlas_multishot.core.stage_manager as stage_manager
from atlas_multishot.ui.stylesheet.style import ATLAS_STYLE
from atlas_multishot.core.utils.user_db import get_assign_json_path

# endregion

# ==========

# region Selection Helpers

def _get_seq_info():
    """Return the parsed sequence info of the current hip file.

    Returns:
        dict | None: Metadata from extract_seq_shot, or None if the hip file
            name cannot be parsed.
    """
    hip_name = os.path.basename(hou.hipFile.name())
    return extract_seq_shot(hip_name)

# endregion

# ==========

# region Selection Panel

class SelectionPanel(QtWidgets.QDialog):
    """Qt dialog that lists the shots assigned to the current artist.

    The artist picks the shot they are working on, which becomes the active
    shot of the /stage network.

    Args:
        parent (QWidget, optional): Parent widget, usually the Houdini main
            window.

    Example:
        from atlas_multishot.ui.selection_ui import SelectionPanel
        dialog = SelectionPanel(hou.qt.mainWindow())
        dialog.show()
    """

    def __init__(self, parent=None):
        super(SelectionPanel, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Atlas ShotSelect v1.0.0 - Houdini")
        self._current_artist  = "Unknown"
        self._sequence_number = None
        self._shots_on_disk   = []
        self._assignments     = {}
        self._selected_shot   = None
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build the widgets, layouts and signal connections."""
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Header
        header = QtWidgets.QLabel("Shot Selection")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        root.addWidget(header)

        # Artist / sequence info
        self._info_label = QtWidgets.QLabel("")
        root.addWidget(self._info_label)

        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(sep)

        # Shot list
        list_label = QtWidgets.QLabel("Your assigned shots:")
        list_label.setStyleSheet("font-weight: bold;")
        root.addWidget(list_label)

        self._shot_list = QtWidgets.QListWidget()
        self._shot_list.setAlternatingRowColors(True)
        self._shot_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        root.addWidget(self._shot_list)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        self._select_btn  = QtWidgets.QPushButton("Set Active Shot")
        self._close_btn   = QtWidgets.QPushButton("Close")
        self._select_btn.setDefault(True)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._select_btn)
        btn_row.addWidget(self._close_btn)
        root.addLayout(btn_row)

        # Status
        self._status = QtWidgets.QLabel("")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(self._status)

        # Signals
        self._refresh_btn.clicked.connect(self._refresh)
        self._select_btn.clicked.connect(self._set_active_shot)
        self._shot_list.itemDoubleClicked.connect(self._set_active_shot)
        self._close_btn.clicked.connect(self.close)
        self.setStyleSheet(ATLAS_STYLE)

        # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _refresh(self):
        """Re-read the artist, sequence, shots on disk and assignments, then rebuild the list."""
        self._current_artist = get_current_artist()
        seq_info = _get_seq_info()

        if seq_info is None:
            self._info_label.setText(
                "Artist: {}   |   Sequence: (could not parse hip name)".format(
                    self._current_artist
                )
            )
            self._set_status("Open a valid seq### hip file first.", error=True)
            return

        self._sequence_number = seq_info["sequence"]
        self._info_label.setText(
            "Artist: {}   |   Sequence: {}".format(
                self._current_artist, self._sequence_number
            )
        )

        self._shots_on_disk = discover_shots(self._sequence_number)
        self._assignments   = assignment_manager.load_assignments(get_assign_json_path())
        my_shots = assignment_manager.get_shots_for_artist(get_assign_json_path(), self._current_artist)

        self._populate_list(my_shots)
        self._set_status(
            "{} shot(s) assigned to you.".format(len(my_shots))
        )

    def _populate_list(self, my_shots):
        """Fill the shot list, highlighting the active shot in green.

        Args:
            my_shots (list[str]): Shot ids assigned to the current artist.
                Shots missing on disk are skipped.
        """
        self._shot_list.clear()

        for shot_id in my_shots:
            if shot_id not in self._shots_on_disk:
                print(
                    "[ShotSetter] WARNING: Assigned shot {} not found on disk. "
                    "Skipping.".format(shot_id)
                )
                continue
            item = QtWidgets.QListWidgetItem(shot_id)
            if shot_id == self._selected_shot:
                item.setForeground(QtGui.QColor("#2ecc71"))
            self._shot_list.addItem(item)

    # ------------------------------------------------------------------
    # Shot activation
    # ------------------------------------------------------------------

    def _set_active_shot(self):
        """Activate the selected shot and update the /stage network, then close."""
        selected_items = self._shot_list.selectedItems()
        if not selected_items:
            self._set_status("Select a shot from the list first.", error=True)
            return

        shot_id = selected_items[0].text()

        if not shot_exists_on_disk(self._sequence_number, shot_id):
            self._set_status(
                "Shot {} does not exist on disk.".format(shot_id), error=True
            )
            return

        self._selected_shot = shot_id

        # Update stage nodes
        stage_manager.apply_node_states(
            shots_on_disk=self._shots_on_disk,
            assignments=self._assignments,
            current_artist=self._current_artist,
            selected_shot=self._selected_shot,
        )

        # Update USD path and shot parameter
        stage_manager.update_usd_path(self._sequence_number, shot_id)
        stage_manager.update_shot_parameter(shot_id)
        stage_manager.update_index_parameter(shot_id)
        stage_manager.update_frame_range(self._sequence_number, shot_id)

        # Refresh colours in list
        self._populate_list(
            assignment_manager.get_shots_for_artist(get_assign_json_path(), self._current_artist)
        )

        self._set_status(
            "Active shot set to: {}".format(shot_id)
        )
        self.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg, error=False):
        """Show a message in the status label.

        Args:
            msg (str): Message to display.
            error (bool): Display the message in the error colour.
        """
        color = "#c0392b" if error else "#27ae60"
        self._status.setStyleSheet("color: {}; font-size: 11px;".format(color))
        self._status.setText(msg)

# endregion

# ==========

# region Module API Helpers

def show_selection_dialog():
    """Launch the Selection Panel as a floating dialog."""
    dialog = SelectionPanel(hou.qt.mainWindow())
    dialog.setMinimumSize(360, 440)
    dialog.show()

# endregion
