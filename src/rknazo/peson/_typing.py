"""
Providing typing stubs.
"""

from os import PathLike
from typing import IO, Any

StrPath = str | PathLike[str]
File = None | int | IO[Any]
