# -*- coding: utf-8 -*-
"""Layer and Compute Extents node discovery for the Atlas USD Writer

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import re

# dcc import
import hou

# atlas modules
import atlas_multishot.core.writer.constants as constants

# endregion

# ==========

# region Layer Discovery

def discover_layers_by_network(shot_num: str) -> dict[str, list[str]]:
    """Discover the active render layers of a shot, grouped by network.

    Bypassed layers are skipped.

    Args:
        shot_num (str): Shot number, plain ('010') or prefixed ('sh010').

    Returns:
        dict[str, list[str]]: Sorted layer names per network, e.g.
            {'SET_LYR': ['BG', 'MG'], 'CHR_LYR': ['CHR01']}.
    """
    m = re.search(r"sh(\d+)$", shot_num)
    shot_num = m.group(1) if m else re.sub(r"^\D+", "", shot_num)

    result: dict[str, list[str]] = {net: [] for net in constants._LAYER_NETWORKS}

    def _collect(node: hou.Node, bucket: list[str]) -> None:
        if node is None:
            return
        for child in node.children():
            match = constants._LAYER_NODE_RE.match(child.name())
            if match:
                if not child.isBypassed():
                    bucket.append(match.group(1))
                else:
                    print(f"[USDWriter] Skipping bypassed layer: {child.path()}")
            _collect(child, bucket)

    for net_name in constants._LAYER_NETWORKS:
        net_path = f"/stage/shot{shot_num}/{net_name}"
        net = hou.node(net_path)
        if net is None:
            print(f"[USDWriter] Network not found: {net_path}")
            continue
        _collect(net, result[net_name])

    for net_name in constants._LAYER_NETWORKS:
        result[net_name] = sorted(set(result[net_name]))

    return result

# endregion

# ==========

# region Compute Extents Discovery

def find_compute_extents_nodes(shot_num: str) -> list[hou.Node]:
    """Find the non-bypassed Compute Extents LOP nodes of a shot.

    Args:
        shot_num (str): Three-digit shot number, e.g. '020'.

    Returns:
        list[hou.Node]: Compute Extents nodes inside /stage/shot{shot_num}, or
            an empty list if that network does not exist.
    """
    root = hou.node(f"/stage/shot{shot_num}")
    if root is None:
        return []
    return [
        n for n in root.allSubChildren()
        if n.type().name() == constants._COMPUTE_EXTENTS_TYPE and not n.isBypassed()
    ]

# endregion
