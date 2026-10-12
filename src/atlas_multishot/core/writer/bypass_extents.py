# -*- coding: utf-8 -*-
"""Compute Extents bypass context manager for the Atlas USD Writer

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# dcc import
import hou

# atlas modules
import atlas_multishot.core.writer.layer_discovery as layer_discovery

# endregion

# ==========

# region Bypass Extents Context Manager

class BypassExtents:
    """Context manager that bypasses the Compute Extents nodes of a shot.

    The nodes are bypassed before the render and restored afterwards, which
    avoids extentsHint.timeSamples bloat in the written USD files.

    Args:
        shot_num (str): Three-digit shot number, e.g. '020'.

    Example:
        with bypass_extents.BypassExtents("020"):
            rop.render()
    """

    def __init__(self, shot_num: str) -> None:
        self._shot_num = shot_num
        self._nodes: list[hou.Node] = []

    def __enter__(self) -> "BypassExtents":
        self._nodes = layer_discovery.find_compute_extents_nodes(self._shot_num)
        for n in self._nodes:
            n.bypass(True)
            print(f"[USDWriter] Bypassed Compute Extents node: {n.path()}")
        return self

    def __exit__(self, *_) -> None:
        for n in self._nodes:
            n.bypass(False)
            print(f"[USDWriter] Restored Compute Extents node: {n.path()}")

# endregion
