"""
Providing utilities to proccess metadata.
"""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from rknazo.peson.types import Metadata

from ._typing import StrPath


def resolve_metadata(metadata: ModuleType) -> Metadata:
    """
    Resolve metadata from module.

    Args:
        metadata (ModuleType): The metadata module to be resolved.

    Returns:
        Metadata: A metadata resolved from module.
    """

    attrs: set[str] = getattr(Metadata, "__protocol_attrs__")

    for attr in attrs:
        if hasattr(metadata, attr):
            continue

        hasdefault = hasattr(Metadata, attr)
        default: Any = getattr(Metadata, attr, None)
        isabstractmethod: bool = getattr(default, "__isabstractmethod__", False)

        if not hasdefault or isabstractmethod:
            raise AttributeError(
                f"Required attribute '{attr}' was not found in metadata '{metadata.__name__}'."
            )

        setattr(metadata, attr, default)

    return cast(Metadata, metadata)


def load_metadata(path: StrPath) -> Metadata:
    """
    Load metadata in challenge.

    Args:
        path (StrPath): The path to challenge.

    Returns:
        Metadata: A metadata loaded from challenge.
    """

    path = Path(path)

    file = path / "metadata.py"

    if not file.exists():
        raise FileNotFoundError(f"metadata for challenge '{path}' was not found.")

    spec = importlib.util.spec_from_file_location(path.name, file)

    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to import metadata from {path}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return resolve_metadata(module)
