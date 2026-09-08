"""
Resolves the `adapter` dotted path in config.yaml to an actual ToolAdapter class.
"""
from __future__ import annotations

import importlib

from .tools.base import ToolAdapter


def resolve_adapter(dotted_path: str) -> type[ToolAdapter]:
    """
    dotted_path example: "reconorch.tools.nmap_adapter.NmapAdapter"
    """
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"invalid adapter path: {dotted_path!r}")

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)

    if not issubclass(cls, ToolAdapter):
        raise TypeError(f"{dotted_path} is not a ToolAdapter subclass")

    return cls
