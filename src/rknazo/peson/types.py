"""
Providing types.
"""

import abc
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Hashable, Protocol, Self

from rknazo.anura.flag import Flag

from ._typing import File, StrPath


@dataclass(frozen=True, kw_only=True)
class Context:
    """
    Challenge context.
    """

    flag: Flag
    """
    Flag.
    """


@dataclass(frozen=True, kw_only=True)
class LoggerConfig:
    """
    Logger configuration.
    """

    name: str
    """
    Logger name.
    """

    stdout: bool = True
    """
    Log stdout.
    """

    stderr: bool = True
    """
    Log stderr.
    """


@dataclass(frozen=True, kw_only=True)
class PrerunProgram:
    """
    Program that runs before the user enters the environment.
    """

    cmd: list[str]
    """
    Command.

    Working directory will be the root directory of artifacts.
    """

    logger: LoggerConfig | bool = True
    """
    Logger configuration.

    If it is a bool, True means it will log stdout and stderr in a file named with `cmd` value, while False means the logger is disabled.
    If it is a LoggerConfig, it will log as configured.
    """

    daemon: bool = False
    """
    Treated as daemon.

    If it is True, the program will restart on exit.
    """


class Package(abc.ABC, Hashable):
    """
    Package.
    """

    @abc.abstractmethod
    def required_packages(self) -> set["Package"]:
        """
        Required packages.
        """

        ...

    @abc.abstractmethod
    def install(self) -> None:
        """
        Install package.
        """

        ...


@dataclass(frozen=True, kw_only=True)
class BuildSettings:
    """
    Settings of build.
    """

    required_packages: set[Package] = field(default_factory=set)
    """
    Required packages.
    """


@dataclass(frozen=True, kw_only=True)
class ProdProperty:
    """
    Challenge property in production environment.

    Dump it to file at build stage, then load it in production environment for setup the environment.
    """

    required_packages: set[Package] = field(default_factory=set)
    """
    Required packages.
    """

    configurations: list[list[str]] = field(default_factory=list)
    """
    Configuration commands.
    """

    prerun_programs: list[PrerunProgram] = field(default_factory=list)
    """
    Pre-run programs.
    """

    def dump(self, path: StrPath, exist_ok: bool = False) -> None:
        """
        Dump property to directory.

        Args:
            path (StrPath): The directory property dumped.
            exist_ok (bool): If it is set to True, the file will be overwritten if it exists.
        """

        file = Path(path) / ".property"

        if not exist_ok and file.exists():
            raise FileExistsError(f"A property file was found in '{path}'.")

        with open(file, "wb") as fp:
            pickle.dump(self, fp)

    @classmethod
    def load(cls, path: StrPath) -> Self:
        """
        Load property from directory.

        Args:
            file (StrPath): The directory to load property.

        Returns:
            Self: Production property loaded from `path`.
        """

        file = Path(path) / ".property"

        if not file.exists():
            raise FileNotFoundError(f"Property file was not found in '{path}'.")

        with open(file, "rb") as fp:
            obj = pickle.load(fp)

        if not isinstance(obj, cls):
            raise TypeError(f"Unexpected type found from data loaded from '{file}'.")

        return obj


@dataclass(frozen=True, kw_only=True)
class BuildResult:
    """
    Challenge build result.
    """

    prop: ProdProperty = ProdProperty()
    """
    Challenge property in production environment.
    """

    artifacts: list[StrPath] = field(default_factory=list)
    """
    Artifacts.

    Artifacts will be moved to the directory as builder configured.
    """


class Metadata(Protocol):
    """
    Challenge metadata.
    """

    settings: BuildSettings = BuildSettings()
    """
    Settings of build.
    """

    @abc.abstractmethod
    def build(self, context: Context) -> BuildResult:
        """
        Build the challenge.
        """

        ...


class Logger(Protocol):
    """
    Logger.
    """

    def __call__(self, config: LoggerConfig) -> tuple[File, File]:
        """
        Make log file IOs from providing logger config.

        Args:
            config (LoggerConfig): The logger config used to make log file IOs.

        Returns:
            tuple[File, File]: File IO (stdout, stderr) in tuple made from `config`.
        """

        ...
