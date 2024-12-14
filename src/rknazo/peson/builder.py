"""
Providing builder.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Sequence

from rknazo.anura.flag import Flag
from rknazo.peson.metadata import load_metadata
from rknazo.peson.types import Context, Package

from ._typing import StrPath


class Builder:
    """
    Challenge builder.
    """

    _installed_packages: set[Package]
    """
    Installed packages.
    """

    def _install_packages(self, packages: set[Package]) -> None:
        """
        Install packages.

        Args:
            packages (set[Package]): The package to install.
        """

        packages = packages.difference(self._installed_packages)

        for package in packages:
            required = package.required_packages()
            self._install_packages(required)

            package.install()

            self._installed_packages.add(package)

    def build(self, source: StrPath, flag: Flag, outdir: StrPath, exist_ok: bool = False) -> None:
        """
        Build challenge with given flag to given output directory.

        Args:
            source (StrPath): Path to challenge.
            flags (Flag): The flag used to build challenge.
            outdir (StrPath): The directory of artifacts.
            exist_ok (bool, optional): If it is set to True, the directory of artifacts will be removed before build if it exists. Defaults to False.
        """

        source = Path(source)
        outdir = Path(outdir)

        if outdir.exists():
            if exist_ok:
                if outdir.is_dir():
                    shutil.rmtree(outdir)
                else:
                    outdir.unlink()
            else:
                raise FileExistsError(f"Directory or file '{outdir}' already exists.")

        outdir.mkdir(parents=True)

        with tempfile.TemporaryDirectory() as root:
            root = Path(root)

            shutil.copytree(source, root, dirs_exist_ok=True)

            metadata = load_metadata(root)
            context = Context(flag=flag)

            self._install_packages(metadata.settings.required_packages)

            cwd = os.getcwd()
            os.chdir(root)

            try:
                result = metadata.build(context)
                artifacts = [os.path.abspath(artifact) for artifact in result.artifacts]
            finally:
                os.chdir(cwd)

            for artifact in artifacts:
                shutil.move(artifact, outdir)

            result.prop.dump(outdir)

    def build_all(
        self,
        sources: Sequence[StrPath],
        flags: Sequence[Flag],
        outdir: StrPath,
        exist_ok: bool = False,
    ) -> None:
        """
        Build challenges with given flags to given output directory.

        Args:
            sources (Sequence[StrPath]): Paths to challenges.
            flags (Sequence[Flag]): The flags used to build challenges.
            outdir (StrPath): The directory of artifacts.
            exist_ok (bool, optional): If it is set to True, the directory of artifacts will be removed before build if it exists. Defaults to False.
        """

        outdir = Path(outdir)

        if outdir.exists():
            if exist_ok:
                shutil.rmtree(outdir)
            else:
                raise FileExistsError(f"Directory or file '{outdir}' already exists.")

        if len(flags) != len(sources):
            raise ValueError("Too many or too few flags for challenges.")

        for source, flag in zip(sources, flags):
            source = Path(source)

            target = outdir / source.name
            self.build(source, flag, target)

    def __init__(self) -> None:
        """
        Initialize the builder.
        """

        self._installed_packages = set()
