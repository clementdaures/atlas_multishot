# -*- coding: utf-8 -*-
"""Shared constants for the Atlas USD Writer

Layer network names, layer node pattern, storage roots, AOV suffixes and the
Cryptomatte parameter name.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Imports & Config

# python modules
import re

_LAYER_NETWORKS = ["SET_LYR", "CHR_LYR"]
_LAYER_NODE_RE  = re.compile(r"^(.+)_lyr$")

_BASE_STORAGE = "//tls-storage02/Prod/ANDHA/05_SHOT"
_WIN_STORAGE  = "P:/ANDHA/05_SHOT"

_AOV_SUFFIXES = ["Ci", "Ut", "Dp"]

_CRYPTO_PARM = "xn__risamplefilter0PxrCryptomattefilename_70bno"

_COMPUTE_EXTENTS_TYPE = "computeextents"

# endregion
