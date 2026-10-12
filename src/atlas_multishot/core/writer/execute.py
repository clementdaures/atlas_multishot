# -*- coding: utf-8 -*-
"""ROP execution helpers for the Atlas USD Writer

Configures and triggers the Cryptomatte filename and the USD ROPs of a render
layer.

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
import atlas_manager.plugins.lighting.core.writer.constants as constants

# endregion

# ==========

# region Execution Helpers

def ensure_dir(path: str) -> None:
    """Create a directory if it does not exist.

    Args:
        path (str): Directory path to create.
    """
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            print(f"[USDWriter] Created directory: {path}")
        except OSError as exc:
            print(f"[USDWriter] WARNING: Cannot create directory {path}: {exc}")


def any_rop_exists(renderlayer: str, stage_node: hou.Node) -> bool:
    """Check whether at least one RDR_OUT_{renderlayer}_{aov} node exists.

    Args:
        renderlayer (str): Render layer name, e.g. 'BG'.
        stage_node (hou.Node): The /stage network.

    Returns:
        bool: True if at least one matching ROP exists.
    """
    return any(
        stage_node.node(f"RDR_OUT_{renderlayer}_{aov}") is not None
        for aov in constants._AOV_SUFFIXES
    )

# endregion

# ==========

# region Cryptomatte

def execute_cryptomatte(
    sequence: str,
    shot: str,
    renderlayer: str,
    stage_node: hou.Node,
) -> None:
    """Set up the Cryptomatte output directory and filename for one layer.

    The layer is skipped if its CRYPTO_{renderlayer} node is missing or
    bypassed.

    Args:
        sequence (str): Zero-padded sequence number, e.g. '010'.
        shot (str): Three-digit shot number, e.g. '020'.
        renderlayer (str): Render layer name, e.g. 'BG'.
        stage_node (hou.Node): The /stage network, passed in to avoid
            repeated hou.node() calls.
    """
    crypto_node = stage_node.node(f"CRYPTO_{renderlayer}")

    if crypto_node is None:
        print(f"[USDWriter] /stage/CRYPTO_{renderlayer} not found — skipping cryptomatte.")
        return
    if crypto_node.isBypassed():
        print(f"[USDWriter] /stage/CRYPTO_{renderlayer} is bypassed — skipping.")
        return

    dir_path = (
        f"{constants._BASE_STORAGE}/SEQ_{sequence}/seq{sequence}sh{shot}"
        f"/rdr/houdini/render/live"
        f"/live_seq{sequence}sh{shot}_{renderlayer}_crypto/"
    )
    ensure_dir(dir_path)

    filename = f"{dir_path}live_seq{sequence}sh{shot}_{renderlayer}_crypto.$F4.exr"

    parm = crypto_node.parm(constants._CRYPTO_PARM)
    if parm is None:
        print(
            f"[USDWriter] WARNING: Cryptomatte parm '{constants._CRYPTO_PARM}' not found "
            f"on /stage/CRYPTO_{renderlayer}. "
            f"Available parms: {[p.name() for p in crypto_node.parms()]}"
        )
    else:
        parm.set(filename)
        print(f"[USDWriter] Cryptomatte filename set: {filename}")

# endregion

# ==========

# region USD ROP

def execute_usd_rop(
    sequence: str,
    shot: str,
    renderlayer: str,
    frame_config: dict,
    stage_node: hou.Node,
) -> bool:
    """Configure and trigger each RDR_OUT_{renderlayer}_{aov} ROP.

    Args:
        sequence (str): Zero-padded sequence number, e.g. '010'.
        shot (str): Three-digit shot number, e.g. '020'.
        renderlayer (str): Render layer name, e.g. 'BG'.
        frame_config (dict): Frame settings with the keys 'single' (bool),
            'start', 'end' and 'step'.
        stage_node (hou.Node): The /stage network, passed in to avoid
            repeated hou.node() calls.

    Returns:
        bool: True if at least one ROP rendered successfully.

    Raises:
        Exception: Any error raised by a ROP render is re-raised.
    """
    any_rendered = False

    for aov in constants._AOV_SUFFIXES:
        rop_name = f"RDR_OUT_{renderlayer}_{aov}"
        rop = stage_node.node(rop_name)
        if rop is None:
            print(
                f"[USDWriter] ROP not found: /stage/{rop_name} — "
                f"no RDR_OUT node for layer '{renderlayer}' / AOV '{aov}'."
            )
            continue

        output_path = (
            f"{constants._WIN_STORAGE}/SEQ_{sequence}/seq{sequence}sh{shot}"
            f"/rdr/houdini/live"
            f"/live_seq{sequence}sh{shot}_{renderlayer}_{aov}.usda"
        )

        lop_parm = rop.parm("lopoutput")
        if lop_parm is None:
            print(f"[USDWriter] WARNING: 'lopoutput' not found on {rop.path()}.")
            continue
        lop_parm.set(output_path)
        print(f"[USDWriter] lopoutput → {output_path}")

        # ── Frame range ──────────────────────────────────────────────────
        if frame_config.get("single"):
            rop.parm("trange").set(0)
            render_kwargs: dict = {}
            print(f"[USDWriter] Frame range: single (frame {hou.frame()})")
        else:
            start = float(frame_config["start"])
            end   = float(frame_config["end"])
            step  = float(frame_config["step"])

            rop.parm("trange").set(1)
            rop.parmTuple("f").set((start, end, step))
            render_kwargs = {"frame_range": (start, end, step)}
            print(f"[USDWriter] Frame range: {int(start)} - {int(end)} - {int(step)}")

        print(f"[USDWriter] Executing Save to Disk on {rop.path()} ...")
        try:
            rop.render(**render_kwargs)
            any_rendered = True
        except Exception as exc:
            print(f"[USDWriter] ERROR during render on {rop.path()}: {exc}")
            raise

    return any_rendered

# endregion
