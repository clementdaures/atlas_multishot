# -*- coding: utf-8 -*-
"""Shot discovery utilities

Scans the project directory tree to discover the existing shots of a sequence.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import os
import re

# Pattern: seqXXXshYYY  (case-insensitive)
_SHOT_DIR_PATTERN = re.compile(r"^seq(\d{3})sh(\d{3})$", re.IGNORECASE)

# endregion

# ==========

# region Shot Discovery

def get_shot_root(sequence_number):
    """Return the root path of a sequence on disk.

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.

    Returns:
        str: Absolute path P:/ANDHA/05_SHOT/SEQ_XXX/.
    """
    return "P:/ANDHA/05_SHOT/SEQ_{}/".format(sequence_number)


def discover_shots(sequence_number):
    """Scan the sequence directory and return all shot folder names found.

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.

    Returns:
        list[str]: Sorted shot identifiers, e.g. ['seq010sh020', 'seq010sh030'].
            Empty if the directory does not exist or is unreadable.
    """
    root = get_shot_root(sequence_number)

    if not os.path.isdir(root):
        print(
            "[ShotSetter] WARNING: Sequence directory not found: {}".format(root)
        )
        return []

    shots = []
    try:
        for entry in os.listdir(root):
            m = _SHOT_DIR_PATTERN.match(entry)
            if m:
                shots.append(entry.lower())
    except OSError as exc:
        print("[ShotSetter] WARNING: Cannot read directory {}: {}".format(root, exc))

    return sorted(shots)


def shot_exists_on_disk(sequence_number, shot_id):
    """Check whether a specific shot directory exists on disk.

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.

    Returns:
        bool: True if the shot directory exists.
    """
    root = get_shot_root(sequence_number)
    path = os.path.join(root, shot_id)
    return os.path.isdir(path)

# endregion
