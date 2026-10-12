# -*- coding: utf-8 -*-
"""Hip file helpers for the Atlas USD Writer

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import os

# dcc import
import hou

# atlas modules
import atlas_multishot.core.utils.parse_sequence as parse_sequence

# endregion

# ==========

# region Hip Helpers

def get_seq_info() -> dict | None:
    """Return the sequence and shot metadata of the current hip file.

    Returns:
        dict | None: Metadata from parse_sequence.extract_seq_shot, or None
            if the hip file name cannot be parsed.
    """
    hip_name = os.path.basename(hou.hipFile.name())
    return parse_sequence.extract_seq_shot(hip_name)

# endregion
