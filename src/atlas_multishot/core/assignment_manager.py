# -*- coding: utf-8 -*-
"""Shot assignment manager

Reads and writes the shot assignment data stored in shot_assign.json.

JSON structure:
    {
        "seq010sh020": "Clement Daures",
        "seq010sh030": "Pablo Rodriguez"
    }

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import json
import os

# endregion

# ==========

# region File Helpers

def _ensure_dir(filepath):
    """Create the parent directory of a file path if it does not exist.

    Args:
        filepath (str): Path of the file about to be written.
    """
    directory = os.path.dirname(filepath)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)

# endregion

# ==========

# region Assignment API

def load_assignments(assign_json_path):
    """Load the current shot assignments from disk.

    Args:
        assign_json_path (str): Path to shot_assign.json.

    Returns:
        dict: Mapping of {shot_id: artist_name}, or an empty dict if the file
            does not exist or is unreadable.
    """
    if not os.path.isfile(assign_json_path):
        return {}

    try:
        with open(assign_json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
            print("[ShotSetter] WARNING: Unexpected format in shot_assign.json.")
            return {}
    except (json.JSONDecodeError, OSError) as exc:
        print("[ShotSetter] WARNING: Cannot load shot_assign.json: {}".format(exc))
        return {}


def save_assignments(assign_json_path, assignments):
    """Persist the shot assignments to disk.

    Args:
        assign_json_path (str): Path to shot_assign.json.
        assignments (dict): Mapping of {shot_id: artist_name}.

    Returns:
        bool: True on success, False on failure.
    """
    try:
        _ensure_dir(assign_json_path)
        with open(assign_json_path, "w", encoding="utf-8") as fh:
            json.dump(assignments, fh, indent=4, ensure_ascii=False)
        print("[ShotSetter] Assignments saved to: {}".format(assign_json_path))
        return True
    except OSError as exc:
        print("[ShotSetter] ERROR: Cannot save shot_assign.json: {}".format(exc))
        return False


def assign_shot(assign_json_path, shot_id, artist_name):
    """Assign a single shot to an artist and save immediately.

    Args:
        assign_json_path (str): Path to shot_assign.json.
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
        artist_name (str): Artist name, e.g. 'Clement Daures'.

    Returns:
        bool: True on success, False on failure.
    """
    assignments = load_assignments(assign_json_path)
    assignments[shot_id] = artist_name
    return save_assignments(assign_json_path, assignments)


def get_shots_for_artist(assign_json_path, artist_name):
    """Return all shots assigned to a given artist.

    Args:
        assign_json_path (str): Path to shot_assign.json.
        artist_name (str): Artist to look up.

    Returns:
        list[str]: Sorted shot ids assigned to that artist.
    """
    assignments = load_assignments(assign_json_path)
    return sorted(
        shot for shot, artist in assignments.items() if artist == artist_name
    )

# endregion
