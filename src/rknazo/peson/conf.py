"""
Providing production environment configurator.
"""

import subprocess
from typing import Iterable

from rknazo.peson.types import Package, ProdProperty

from ._typing import StrPath


class Configurator:
    """
    Production environment configurator.
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

    def configure(self, path: StrPath) -> None:
        """
        Configure production environment for challenge.

        Args:
            path (StrPath): Path to built challenge.
        """

        prop = ProdProperty.load(path)

        for cmd in prop.configurations:
            subprocess.check_call(cmd, cwd=path)

        self._install_packages(prop.required_packages)

    def configure_all(self, paths: Iterable[StrPath]) -> None:
        """
        Configure production environment for challenges.

        Args:
            paths (Iterable[StrPath]): Paths to built challenge.
        """

        for path in paths:
            self.configure(path)

    def __init__(self) -> None:
        """
        Initialize production environment configurator.
        """

        self._installed_packages = set()
