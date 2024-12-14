"""
Providing builtin logger implements.
"""

import sys
from pathlib import Path

from rknazo.peson.types import Logger, LoggerConfig

from ._typing import File, StrPath


def standard_logger() -> Logger:
    """
    Logging to stdout and stderr.

    `name` in logger config will be ignored.

    Returns:
        Logger: A logger logging to stdout and stderr.
    """

    def logger(config: LoggerConfig) -> tuple[File, File]:
        return (
            sys.stdout if config.stdout else None,
            sys.stderr if config.stderr else None,
        )

    return logger


def file_logger(root: StrPath, split: bool = True) -> Logger:
    """
    Logging to file with name as configured in specific directory.

    Args:
        root (StrPath): The logger root directory.
        split (bool, optional): If it is set to True, stdout and stderr will log to seperate file respectively. Defaults to True.

    Returns:
        Logger: A logger logging to file with name as configured in `root` directory.
    """

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    def logger(config: LoggerConfig) -> tuple[File, File]:
        if not config.stdout and not config.stderr:
            return (None, None)

        if not split:
            path = (root / config.name).with_suffix(".log")
            fp = open(path, "w")
            return (fp if config.stdout else None, fp if config.stderr else None)

        stdout, stderr = None, None

        if config.stdout:
            name = config.name + "-stdout"
            path = (root / name).with_suffix(".log")
            stdout = open(path, "w")

        if config.stderr:
            name = config.name + "-stderr"
            path = (root / name).with_suffix(".log")
            stderr = open(path, "w")

        return (stdout, stderr)

    return logger
