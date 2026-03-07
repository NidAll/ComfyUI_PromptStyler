"""
ComfyUI PromptStyler custom nodes.

Drop this folder into: ComfyUI/custom_nodes/ComfyUI_PromptStyler
Then restart ComfyUI (or use "Reload custom nodes").
"""

from __future__ import annotations

import os


def _read_version() -> str:
    here = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(here, "VERSION"), "r", encoding="utf-8") as handle:
        return handle.read().strip()


__version__ = _read_version()

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "__version__"]
