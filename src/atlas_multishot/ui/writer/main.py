# -*- coding: utf-8 -*-
"""Atlas multi-shot UI class

This module provides the UI for `Multi-Shot` Lighting, which allows writing
the USD files of several shots from a single .hipnc scene.

For each enabled shot, the tool activates the shot, bypasses the Compute
Extents nodes, sets the Cryptomatte filename and triggers the USD ROPs of
every layer with its own frame range.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import re

# pyside modules
try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore

# dcc import
import hou

# atlas modules
import atlas_manager.plugins.lighting.core.utils.scan_shot as scan_shot
import atlas_manager.plugins.lighting.core.utils.user_db as user_db
import atlas_manager.plugins.lighting.core.assignment_manager as assignment_manager
import atlas_manager.plugins.lighting.core.stage_manager as stage_manager
import atlas_manager.plugins.lighting.ui.stylesheet.style as style
import atlas_manager.plugins.lighting.core.writer.hip_helpers as hip_helpers
import atlas_manager.plugins.lighting.core.writer.layer_discovery as layer_discovery
import atlas_manager.plugins.lighting.core.writer.bypass_extents as bypass_extents
import atlas_manager.plugins.lighting.core.writer.execute as execute
import atlas_manager.plugins.lighting.core.writer.constants as constants
import atlas_manager.plugins.lighting.ui.writer.widget.shot_panel as shot_panel

# endregion

# ==========

# region USD Writer Panel

class USDWriterPanel(QtWidgets.QDialog):
    """Qt dialog for the multi-shot USD export.

    One collapsible panel is built per shot assigned to the current artist,
    each containing its SET and CHR layers with editable frame ranges.

    Args:
        parent (QWidget, optional): Parent widget, usually the Houdini main
            window.

    Example:
        from atlas_multishot.ui.writer.main import USDWriterPanel
        dialog = USDWriterPanel(hou.qt.mainWindow())
        dialog.show()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Atlas Multishot v1.0.0 - Houdini")
        self._seq_info:      dict | None  = None
        self._shot_panels:   list         = []
        self._shots_on_disk: list[str]    = []
        self._assignments:   dict         = {}
        self._artist:        str          = ""
        self._assign_path:   str          = ""
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the widgets, layouts and signal connections."""
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QtWidgets.QLabel("Multi-Shot USD Writer")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        root.addWidget(header)

        self._info_label = QtWidgets.QLabel("")
        root.addWidget(self._info_label)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        root.addWidget(sep)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._panels_container = QtWidgets.QWidget()
        self._panels_layout    = QtWidgets.QVBoxLayout(self._panels_container)
        self._panels_layout.setContentsMargins(2, 2, 2, 2)
        self._panels_layout.setSpacing(6)
        self._panels_layout.addStretch()
        scroll.setWidget(self._panels_container)
        root.addWidget(scroll)

        btn_row = QtWidgets.QHBoxLayout()
        self._refresh_btn = QtWidgets.QPushButton("Refresh")
        self._refresh_btn.setToolTip("Re-scan shots and layers")
        self._write_btn   = QtWidgets.QPushButton("Write")
        self._write_btn.setDefault(True)
        self._close_btn   = QtWidgets.QPushButton("Close")
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._write_btn)
        btn_row.addWidget(self._close_btn)
        root.addLayout(btn_row)

        self._status = QtWidgets.QLabel("")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(self._status)

        self._refresh_btn.clicked.connect(self._refresh)
        self._write_btn.clicked.connect(self._multi_write)
        self._close_btn.clicked.connect(self.close)
        self.setStyleSheet(style.ATLAS_STYLE)

    # ------------------------------------------------------------------
    # Refresh / scan
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        """Re-scan the sequence, shots, assignments and layers, then rebuild the shot panels."""
        self._seq_info = hip_helpers.get_seq_info()
        if self._seq_info is None:
            self._info_label.setText("Cannot parse sequence from hip file name.")
            self._set_status("Open a valid seq### hip file first.", error=True)
            return

        sequence = self._seq_info["sequence"]

        self._artist      = user_db.get_current_artist()
        self._assign_path = user_db.get_assign_json_path()
        self._info_label.setText(f"Sequence: {sequence}   |   Artist: {self._artist}")

        self._shots_on_disk = scan_shot.discover_shots(sequence)
        self._assignments   = assignment_manager.load_assignments(self._assign_path)
        my_shots = assignment_manager.get_shots_for_artist(self._assign_path, self._artist)

        total_layers = self._build_shot_panels(my_shots)

        if not my_shots:
            self._set_status("No shots assigned to you for this sequence.", error=True)
        else:
            self._set_status(
                f"{len(my_shots)} shot(s) | {total_layers} active layer(s) discovered."
            )

    def _build_shot_panels(self, shot_ids: list[str]) -> int:
        """Rebuild the list of shot panels.

        The frame range of each shot is read from its frame_range.json and
        falls back to the Houdini timeline when the file is missing.

        Args:
            shot_ids (list[str]): Shot ids to build a panel for.

        Returns:
            int: Total number of active layers across all shots.
        """
        self._shot_panels.clear()
        while self._panels_layout.count() > 1:
            item = self._panels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_layers = 0

        timeline_start, timeline_end = hou.playbar.frameRange()

        for shot_id in shot_ids:
            m = re.search(r"sh(\d+)$", shot_id)
            if not m:
                print(f"[USDWriter] Cannot parse shot number from: {shot_id}")
                continue

            shot_num = m.group(1)
            by_net = layer_discovery.discover_layers_by_network(shot_num)
            total_layers += sum(len(v) for v in by_net.values())

            seq = self._seq_info["sequence"]
            json_path = (
                f"{constants._BASE_STORAGE}/SEQ_{seq}/seq{seq}sh{shot_num}"
                f"/asb/houdini/live/frame_range.json"
            )
            try:
                start, end = stage_manager.get_frame_range_from_json(json_path)
                print(f"[USDWriter] [{shot_id}] Frame range from JSON: {start}-{end}")
            except (FileNotFoundError, KeyError):
                start, end = int(timeline_start), int(timeline_end)
                print(f"[USDWriter] [{shot_id}] Frame range fallback to timeline: {start}-{end}")

            panel = shot_panel.ShotPanel(
                shot_id,
                set_layers=by_net["SET_LYR"],
                chr_layers=by_net["CHR_LYR"],
                start=start,
                end=end,
            )
            self._shot_panels.append(panel)
            self._panels_layout.insertWidget(self._panels_layout.count() - 1, panel)

        return total_layers

    # ------------------------------------------------------------------
    # Shot activation
    # ------------------------------------------------------------------

    def _activate_shot(self, shot_id: str) -> None:
        """Set the active shot before its layers are written.

        Updates the node states, the USD path, the shot and shot_index
        parameters and the timeline. Called once per shot.

        Args:
            shot_id (str): Shot identifier, e.g. 'seq010sh020'.
        """
        print(f"[USDWriter] Active shot set to: {shot_id}")
        if self._seq_info is None:
            return

        stage_manager.apply_node_states(
            shots_on_disk=self._shots_on_disk,
            assignments=self._assignments,
            current_artist=self._artist,
            selected_shot=shot_id,
        )
        stage_manager.update_usd_path(self._seq_info["sequence"], shot_id)
        stage_manager.update_shot_parameter(shot_id)
        stage_manager.update_index_parameter(shot_id)
        stage_manager.update_frame_range(self._seq_info["sequence"], shot_id)

    # ------------------------------------------------------------------
    # Multi-Write execution
    # ------------------------------------------------------------------

    def _multi_write(self) -> None:
        """Write the USD layers of every enabled shot.

        For each layer, the Cryptomatte filename is set (step A) and the USD
        ROPs are rendered (step B). Errors are collected, printed to the
        console and summarised in the status label.
        """
        if self._seq_info is None:
            self._set_status("No sequence info available.", error=True)
            return

        sequence = self._seq_info["sequence"]
        errors: list[str] = []
        written = 0

        for panel in self._shot_panels:
            if not panel.is_enabled():
                continue

            shot_id = panel.shot_id
            m = re.search(r"sh(\d+)$", shot_id)
            if not m:
                errors.append(f"Cannot parse shot number from: {shot_id}")
                continue
            shot = m.group(1)

            self._activate_shot(shot_id)

            stage_node = hou.node("/stage")
            if stage_node is None:
                errors.append(f"[{shot_id}] /stage node not found — skipping.")
                continue

            with bypass_extents.BypassExtents(shot):

                for renderlayer, frame_cfg in panel.layer_configs():

                    if not execute.any_rop_exists(renderlayer, stage_node):
                        print(
                            f"[USDWriter] No RDR_OUT nodes for '{renderlayer}' — "
                            f"skipping cryptomatte and render."
                        )
                        continue

                    # ── Step A : Cryptomatte ─────────────────────────────
                    try:
                        execute.execute_cryptomatte(sequence, shot, renderlayer, stage_node)
                    except Exception as exc:
                        errors.append(f"Cryptomatte error [{shot_id}/{renderlayer}]: {exc}")

                    # ── Step B : USD ROP ─────────────────────────────────
                    try:
                        rendered = execute.execute_usd_rop(
                            sequence, shot, renderlayer, frame_cfg, stage_node
                        )
                        if rendered:
                            written += 1
                    except Exception as exc:
                        errors.append(f"USD ROP error [{shot_id}/{renderlayer}]: {exc}")

        if errors:
            for err in errors:
                print(f"[USDWriter] ERROR: {err}")
            self._set_status(
                f"{written} layer(s) written. {len(errors)} error(s) — see console.",
                error=True,
            )
        else:
            self._set_status(f"Done. {written} USD layer(s) written successfully.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str, error: bool = False) -> None:
        """Show a message in the status label.

        Args:
            msg (str): Message to display.
            error (bool): Display the message in the error colour.
        """
        color = "#c0392b" if error else "#27ae60"
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._status.setText(msg)

# endregion

# ==========

# region Module API Helpers

def show_usd_writer_dialog() -> None:
    """Launch the USD Writer Panel as a floating dialog."""
    dialog = USDWriterPanel(hou.qt.mainWindow())
    dialog.setMinimumSize(520, 560)
    dialog.show()

# endregion
