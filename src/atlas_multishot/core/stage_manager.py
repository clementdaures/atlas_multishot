# -*- coding: utf-8 -*-
"""Stage manager utilities for Houdini Solaris

Manages the /stage shot{XXX} nodes and drives the /stage/shot_asb and
/stage/LIGHTING_CTL parameters (USD path, shot, shot index, sequence and
frame range) from the assignment and selection state.

Node colour conventions:
    Black: shot does not exist on disk, or is assigned to another artist.
    Red: shot is assigned to the current artist but is not the active shot.
    Green: shot is assigned to the current artist and is the active shot.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import json

# dcc import
import hou

# Node colours (R, G, B) in 0-1 range
_COLOR_BLACK = hou.Color((0.0, 0.0, 0.0))
_COLOR_RED   = hou.Color((0.6, 0.08, 0.08))
_COLOR_GREEN = hou.Color((0.15, 0.55, 0.15))

# endregion

# ==========

# region Stage Helpers

def _get_stage():
    """Return the /stage network.

    Returns:
        hou.Node | None: The /stage node, or None if it does not exist.
    """
    node = hou.node("/stage")
    if node is None:
        print("[ShotSetter] WARNING: /stage not found.")
    return node


def _get_shot_node(stage, shot_id):
    """Find the shot{XXX} node matching a shot id.

    Args:
        stage (hou.Node): The /stage network.
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.

    Returns:
        hou.Node | None: The matching node, or None if it is not found.
    """
    shot_number = shot_id[-3:]
    node_name = "shot{}".format(shot_number)
    node = stage.node(node_name)
    if node is None:
        print(
            "[ShotSetter] WARNING: Node /stage/{} not found. Skipping.".format(node_name)
        )
    return node


def _set_bypassed(node, bypassed):
    """Set the bypass flag on a node, printing a warning on failure.

    Args:
        node (hou.Node): Node to modify.
        bypassed (bool): Desired bypass state.
    """
    try:
        node.bypass(bypassed)
    except Exception as exc:
        print(
            "[ShotSetter] WARNING: Cannot set bypass on {}: {}".format(
                node.path(), exc
            )
        )


def _set_color(node, color):
    """Set the colour of a node, printing a warning on failure.

    Args:
        node (hou.Node): Node to modify.
        color (hou.Color): Desired node colour.
    """
    try:
        node.setColor(color)
    except Exception as exc:
        print(
            "[ShotSetter] WARNING: Cannot set color on {}: {}".format(
                node.path(), exc
            )
        )

# endregion

# ==========

# region Node States

def apply_node_states(shots_on_disk, assignments, current_artist, selected_shot):
    """Apply bypass state and colour to every /stage/shot{XXX} node.

    Rules:
        - No disk directory found: bypass on, colour black.
        - Assigned to another artist: bypass on, colour black.
        - Assigned to the current artist, not selected: bypass off, colour red.
        - Assigned to the current artist, selected: bypass off, colour green.

    Args:
        shots_on_disk (list[str]): Shot ids confirmed to exist on disk.
        assignments (dict): Mapping of {shot_id: artist_name}.
        current_artist (str): Logged-in artist name.
        selected_shot (str | None): Currently selected shot id.
    """
    stage = _get_stage()
    if stage is None:
        return

    shots_on_disk_set = set(shots_on_disk)

    for node in stage.children():
        name = node.name()
        if not name.startswith("shot"):
            continue
        # Avoid accidental matches like "shot_asb"
        suffix = name[len("shot"):]
        if not suffix.isdigit():
            continue

        shot_number = suffix  # e.g. '020'

        # Reconstruct full shot_id by matching against discovered shots
        matching = [s for s in shots_on_disk_set if s.endswith("sh" + shot_number)]

        if not matching:
            # No disk directory -> bypass + black
            print(
                "[ShotSetter] WARNING: No disk directory found for node /stage/{}, "
                "shot have been bypass.".format(name)
            )
            _set_bypassed(node, True)
            _set_color(node, _COLOR_BLACK)
            continue

        shot_id = matching[0]
        assigned_artist = assignments.get(shot_id)

        if assigned_artist != current_artist:
            # Not the current user's shot -> bypass + black
            _set_bypassed(node, True)
            _set_color(node, _COLOR_BLACK)
        elif shot_id == selected_shot:
            # Assigned AND selected -> unbypass + green
            _set_bypassed(node, False)
            _set_color(node, _COLOR_GREEN)
        else:
            # Assigned but not selected -> unbypass + red
            _set_bypassed(node, False)
            _set_color(node, _COLOR_RED)

# endregion

# ==========

# region Stage Parameters

def update_usd_path(sequence_number, shot_id):
    """Update /stage/shot_asb filepath1 with the live USD path of a shot.

    The path follows the template
    $JOB/05_SHOT/SEQ_XXX/seqXXXshYYY/asb/houdini/live/live_seqXXXshYYY_asb.usda

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
    """
    node = hou.node("/stage/shot_asb")
    if node is None:
        print("[ShotSetter] WARNING: /stage/shot_asb not found. Cannot update USD path.")
        return

    shot_number = shot_id[-3:]
    seq = sequence_number

    usd_path = (
        "$JOB/05_SHOT/SEQ_{seq}/seq{seq}sh{shot}/"
        "asb/houdini/live/live_seq{seq}sh{shot}_asb.usda"
    ).format(seq=seq, shot=shot_number)

    try:
        parm = node.parm("filepath1")
        if parm is None:
            print(
                "[ShotSetter] WARNING: Parameter 'filepath1' not found on /stage/shot_asb."
            )
            return
        parm.set(usd_path)
        print("[ShotSetter] USD path updated: {}".format(usd_path))
    except Exception as exc:
        print("[ShotSetter] ERROR: Cannot update filepath1: {}".format(exc))


def update_shot_parameter(shot_id):
    """Set the 'shot' parameter on /stage/LIGHTING_CTL.

    The parameter receives the three-digit shot number (e.g. '020').

    Args:
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
    """
    ctrl = hou.node("/stage/LIGHTING_CTL")
    if ctrl is None:
        print("[ShotSetter] WARNING: /stage/LIGHTING_CTL not found. Cannot update shot parameter.")
        return

    shot_number = shot_id[-3:]  # e.g. '020'

    try:
        parm = ctrl.parm("shot")
        if parm is None:
            print(
                "[ShotSetter] WARNING: Parameter 'shot' not found on /stage/LIGHTING_CTL."
            )
            return
        parm.set(shot_number)
        print("[ShotSetter] LIGHTING_CTL shot parameter updated: {}".format(shot_number))
    except Exception as exc:
        print("[ShotSetter] ERROR: Cannot update shot parameter: {}".format(exc))

def update_index_parameter(shot_id):
    """Set the 'shot_index' parameter on /stage/LIGHTING_CTL.

    The parameter receives the shot node name (e.g. 'shot020').

    Args:
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
    """
    ctrl = hou.node("/stage/LIGHTING_CTL")
    if ctrl is None:
        print("[ShotSetter] WARNING: /stage/LIGHTING_CTL not found. Cannot update shot parameter.")
        return

    shot_number = shot_id[-3:]  # e.g. '020'

    try:
        parm = ctrl.parm("shot_index")
        if parm is None:
            print(
                "[ShotSetter] WARNING: Parameter 'shot' not found on /stage/LIGHTING_CTL."
            )
            return
        parm.set(f"shot{shot_number}")
        print("[ShotSetter] LIGHTING_CTL shot parameter updated: {}".format(shot_number))
    except Exception as exc:
        print("[ShotSetter] ERROR: Cannot update shot parameter: {}".format(exc))


def update_sequence_parameter(sequence_number):
    """Set the 'sequence' parameter on /stage/LIGHTING_CTL.

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.
    """
    ctrl = hou.node("/stage/LIGHTING_CTL")
    if ctrl is None:
        print("[ShotSetter] WARNING: /stage/LIGHTING_CTL not found. Cannot update sequence parameter.")
        return

    try:
        parm = ctrl.parm("sequence")
        if parm is None:
            print(
                "[ShotSetter] WARNING: Parameter 'sequence' not found on /stage/LIGHTING_CTL."
            )
            return
        parm.set(sequence_number)
        print("[ShotSetter] LIGHTING_CTL sequence parameter updated: {}".format(sequence_number))
    except Exception as exc:
        print("[ShotSetter] ERROR: Cannot update sequence parameter: {}".format(exc))

# endregion

# ==========

# region Frame Range

def get_frame_range_from_json(file_path):
    """Read the start and end frames from a frame_range.json file.

    Args:
        file_path (str): Full path to the frame_range.json file.

    Returns:
        tuple[int, int]: The (start_frame, end_frame) pair.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the expected keys are missing from the file.
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    start_frame = data["start_frame"]
    end_frame = data["end_frame"]

    print(f"Loaded frame range {start_frame}-{end_frame} from: {file_path}")
    return start_frame, end_frame


def update_frame_range(sequence_number, shot_id):
    """Set the Houdini timeline to the frame range of a shot.

    The range is read from the shot's live frame_range.json. If the file is
    missing or invalid, the timeline is left unchanged.

    Args:
        sequence_number (str): Zero-padded sequence number, e.g. '010'.
        shot_id (str): Shot identifier, e.g. 'seq010sh020'.
    """
    shot_number = shot_id[-3:]
    seq = sequence_number

    live_path = hou.expandString(
        "$JOB/05_SHOT/SEQ_{seq}/seq{seq}sh{shot}"
        "/asb/houdini/live/frame_range.json".format(seq=seq, shot=shot_number)
    )

    try:
        start_frame, end_frame = get_frame_range_from_json(live_path)
    except (FileNotFoundError, KeyError):
        print(f"[ShotSetter] WARNING: frame_range.json not found at {live_path} — timeline unchanged.")
        return

    hou.playbar.setFrameRange(start_frame, end_frame)
    hou.playbar.setPlaybackRange(start_frame, end_frame)
    print(f"[ShotSetter] Set Houdini timeline to {start_frame}-{end_frame}")

# endregion
