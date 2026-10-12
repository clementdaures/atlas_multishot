# -*- coding: utf-8 -*-
"""Artist database utilities

Loads and queries the users.json artist database, and resolves the
logged-in artist and the data file paths used by the tool.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import json
import os

# dcc import
import hou

# atlas modules
from atlas_manager.objects.guard import Guard

# endregion

# ==========

# region Path Helpers

def get_user_json_path():
    """Return the path of the artist database.

    Uses the project database root when Guard resolves a project, and falls
    back to $HIP otherwise.

    Returns:
        str: Path to users.json.
    """
    guard = Guard()
    if guard.project_root:
        return os.path.join(guard.database_root, "users.json")
    return os.path.join(hou.expandString("$HIP"), "users.json")  # fallback

def get_assign_json_path():
    """Return the path of the shot assignment file.

    Returns:
        str: Path to $HIP/data/shot_assign.json.
    """
    return os.path.join(hou.expandString("$HIP"), "data", "shot_assign.json")

# endregion

# ==========

# region User Database

def load_users(user_json_path):
    """Load the user data from a JSON file.

    Args:
        user_json_path (str): Absolute path to users.json.

    Returns:
        dict: Raw user dictionary, or an empty dict on failure.
    """
    if not os.path.isfile(user_json_path):
        print("[ShotSetter] WARNING: user.json not found at: {}".format(user_json_path))
        return {}

    try:
        with open(user_json_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print("[ShotSetter] WARNING: Cannot load user.json: {}".format(exc))
        return {}


def list_artist_names(user_json_path):
    """Return all artist names from the user database.

    Args:
        user_json_path (str): Absolute path to users.json.

    Returns:
        list[str]: Sorted artist names.
    """
    users = load_users(user_json_path)
    return sorted(users.keys())


def get_current_artist():
    """Retrieve the name of the logged-in artist through Guard.

    Returns:
        str: Artist name, or 'Unknown' if unavailable.
    """
    try:
        from atlas_manager.objects.guard import Guard
        guard = Guard()
        return guard.user if guard.user else "Unknown"
    except Exception:
        return "Unknown"

# endregion
