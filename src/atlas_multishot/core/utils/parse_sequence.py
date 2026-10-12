# -*- coding: utf-8 -*-
"""Hip file name parser

Parses Houdini hip file names to extract sequence and shot information.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import re

# Regex patterns
_SHOT_PATTERN = re.compile(r"(seq(\d{3})sh(\d{3}))", re.IGNORECASE)
_GLOBAL_PATTERN = re.compile(r"(seq(\d{3})glb)", re.IGNORECASE)

# endregion

# ==========

# region Sequence Parser

def extract_seq_shot(hip_name):
    """Parse a hip file name and return its sequence and shot metadata.

    Supported patterns:
        seq010sh020: shot scene.
        seq010glb: global scene.

    Args:
        hip_name (str): Hip file name or full path, e.g.
            'seq010sh020_light_v001.hipnc'.

    Returns:
        dict | None: A dict with the keys 'scene_type' ('shot' or 'global'),
            'full_task' (e.g. 'seq010sh020' or 'seq010glb'), 'sequence'
            (e.g. '010') and 'shot' (e.g. '020', or None for a global scene).
            None if no valid pattern is found.
    """
    if not hip_name:
        return None

    # Shot scene
    m = _SHOT_PATTERN.search(hip_name)
    if m:
        return {
            "scene_type": "shot",
            "full_task":  m.group(1).lower(),
            "sequence":   m.group(2),
            "shot":       m.group(3),
        }

    # Global scene
    m = _GLOBAL_PATTERN.search(hip_name)
    if m:
        return {
            "scene_type": "global",
            "full_task":  m.group(1).lower(),
            "sequence":   m.group(2),
            "shot":       None,
        }

    return None

# endregion
