# -*- coding: utf-8 -*-
"""Atlas Multishot package for Houdini Solaris

Public entry points for the multi-shot lighting tool: shot assignment, shot
selection, /stage node state management and multi-shot USD writing.

Author: Clement Daures
Website: clementdaures.com
Created: 2025

Example:
    from atlas_multishot import show_assignment_panel, show_selection_panel
    from atlas_multishot import show_write_panel, apply_all_node_states

    show_assignment_panel()
    show_selection_panel()
    show_write_panel()
"""

# region Imports & Config

# atlas modules
from atlas_multishot.ui.assignment_ui import show_assignment_dialog  as show_assignment_panel
from atlas_multishot.ui.selection_ui import show_selection_dialog   as show_selection_panel
from atlas_multishot.core.stage_manager import apply_node_states       as apply_all_node_states
from atlas_multishot.ui.writer.main import show_usd_writer_dialog  as show_write_panel

# endregion

# ==========

# region Public API

__all__ = [
    "show_assignment_panel",
    "show_selection_panel",
    "apply_all_node_states",
    "show_write_panel",
]

# endregion
