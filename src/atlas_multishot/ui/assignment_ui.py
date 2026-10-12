# -*- coding: utf-8 -*-
"""Atlas shot assignment UI class

This module provides the UI for `Assign Shots` Lighting, which allows a
supervisor or an artist to:
    - see all the shots discovered for the current sequence
    - assign one artist per shot
    - save the result to $HIP/data/shot_assign.json

On launch, the 'sequence' parameter of /stage/LIGHTING_CTL is populated if
the sequence can be parsed from the hip file name.

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
from atlas_manager.plugins.lighting.core.utils.parse_sequence import extract_seq_shot
from atlas_manager.plugins.lighting.core.utils.scan_shot import discover_shots
from atlas_manager.plugins.lighting.core.utils.user_db import list_artist_names
from atlas_manager.plugins.lighting.core.assignment_manager import load_assignments, save_assignments
from atlas_manager.plugins.lighting.core.stage_manager import update_sequence_parameter
from atlas_manager.plugins.lighting.ui.stylesheet.style import ATLAS_STYLE
from atlas_manager.plugins.lighting.core.utils.user_db import get_user_json_path, get_assign_json_path

# endregion

# ==========

# region Assignment Helpers

def _get_current_seq():
    """Return the sequence number of the current hip file.

    Returns:
        str | None: Zero-padded sequence number, or None if the hip file name
            cannot be parsed.
    """
    hip_name = os.path.basename(hou.hipFile.name())
    info = extract_seq_shot(hip_name)
    if info:
        return info["sequence"]
    return None

# endregion

# ==========

# region Assignment Panel

class AssignmentPanel(QtWidgets.QDialog):
    """Qt dialog that lists shots and lets the user assign artists to them.

    Designed to be launched as a floating dialog or embedded as a Houdini
    Python Panel.

    Args:
        parent (QWidget, optional): Parent widget, usually the Houdini main
            window.

    Example:
        from atlas_multishot.ui.assignment_ui import AssignmentPanel
        dialog = AssignmentPanel(hou.qt.mainWindow())
        dialog.show()
    """

    def __init__(self, parent=None):
        super(AssignmentPanel, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Atlas ShotAssign v1.0.0 - Houdini")
        self._assignments = {}
        self._shots       = []
        self._artists     = []
        self._combo_map   = {}
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
        header = QtWidgets.QLabel("Shot Assignment")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        root.addWidget(header)

        # Sequence info label
        self._seq_label = QtWidgets.QLabel("Sequence: —")
        root.addWidget(self._seq_label)

        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(sep)

        # Scroll area for shot rows
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._shot_container = QtWidgets.QWidget()
        self._shot_layout    = QtWidgets.QFormLayout(self._shot_container)
        self._shot_layout.setContentsMargins(4, 4, 4, 4)
        self._shot_layout.setSpacing(6)
        scroll.setWidget(self._shot_container)
        root.addWidget(scroll)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        self._save_btn    = QtWidgets.QPushButton("Save Assignments")
        self._close_btn   = QtWidgets.QPushButton("Close")
        self._save_btn.setDefault(True)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._close_btn)
        root.addLayout(btn_row)

        # Status bar
        self._status = QtWidgets.QLabel("")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(self._status)

        # Signals
        self._refresh_btn.clicked.connect(self._refresh)
        self._save_btn.clicked.connect(self._save)
        self._close_btn.clicked.connect(self.close)
        self.setStyleSheet(ATLAS_STYLE)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _refresh(self):
        """Re-read the sequence, shots, artists and assignments, then rebuild the rows."""
        seq = _get_current_seq()
        if seq is None:
            self._seq_label.setText("Sequence: (could not parse from hip name)")
            self._set_status("Open a seq###glb or seq###sh### hip file first.", error=True)
            return

        self._seq_label.setText("Sequence: {}".format(seq))

        update_sequence_parameter(seq)

        self._shots   = discover_shots(seq)
        self._artists = list_artist_names(get_user_json_path())
        self._assignments = load_assignments(get_assign_json_path())

        self._populate_rows()
        self._set_status(
            "{} shots found.".format(len(self._shots))
        )

    def _populate_rows(self):
        """Rebuild one artist combo box per discovered shot."""
        # Clear existing rows
        while self._shot_layout.rowCount():
            self._shot_layout.removeRow(0)
        self._combo_map.clear()

        if not self._shots:
            self._shot_layout.addRow(
                QtWidgets.QLabel("No shots discovered.")
            )
            return

        artist_options = ["(unassigned)"] + self._artists

        for shot_id in self._shots:
            combo = QtWidgets.QComboBox()
            combo.addItems(artist_options)

            # Pre-select current assignment
            current = self._assignments.get(shot_id, "")
            if current in self._artists:
                idx = artist_options.index(current)
                combo.setCurrentIndex(idx)

            self._combo_map[shot_id] = combo
            self._shot_layout.addRow(shot_id, combo)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self):
        """Write the combo box selections to shot_assign.json and close on success."""
        new_assignments = {}
        for shot_id, combo in self._combo_map.items():
            artist = combo.currentText()
            if artist != "(unassigned)":
                new_assignments[shot_id] = artist

        ok = save_assignments(get_assign_json_path(), new_assignments)
        if ok:
            self._assignments = new_assignments
            self._set_status("Assignments saved successfully.")
            self.close()
        else:
            self._set_status("ERROR: Could not save assignments.", error=True)

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

def show_assignment_dialog():
    """Launch the Assignment Panel as a floating dialog."""
    dialog = AssignmentPanel(hou.qt.mainWindow())
    dialog.setMinimumSize(420, 480)
    dialog.show()

# endregion
