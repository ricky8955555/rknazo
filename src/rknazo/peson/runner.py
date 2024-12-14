"""
Providing production environment runner.
"""

import subprocess
from pathlib import Path
from threading import Thread
from typing import Any, Iterable, Sequence

from rknazo.peson.types import Logger, LoggerConfig, PrerunProgram, ProdProperty

from ._typing import File, StrPath


class Runner:
    """
    Production environment runner.
    """

    challenges: list[tuple[Path, ProdProperty]]
    """
    Path and property of challenges
    """

    logger: Logger
    """
    Logger.
    """

    _processes: list[subprocess.Popen[Any]]
    """
    Running processes.
    """

    _threads: list[Thread]
    """
    Running threads.
    """

    _running: bool
    """
    Is environment running or not.
    """

    def _parse_logger_config(self, program: PrerunProgram) -> tuple[File, File]:
        """
        Parse logger config to file IOs.

        Args:
            program (PrerunProgram): The pre-run program used to parse to log file IOs.

        Returns:
            tuple[File, File]: File IO (stdout, stderr) in tuple parsed from `config` made by configured logger.
        """

        config = program.logger

        if config is False:
            return None, None

        if not isinstance(config, LoggerConfig):
            name = "".join(program.cmd)
            config = LoggerConfig(name=name, stdout=True, stderr=True)

        return self.logger(config)

    def _run_program(self, daemon: bool, *args: Any, **kwargs: Any) -> Thread:
        """
        Run program with status guaranteed.

        Args:
            daemon (bool): Treated as daemon.
            args (Any), kwargs (Any): Arguments for subproess.Popen.

        Returns:
            Thread: A thread used to guarantee process.
        """

        def task() -> None:
            process = None

            while process is None or self._running:
                process = subprocess.Popen(*args, **kwargs)
                self._processes.append(process)

                process.wait()
                self._processes.remove(process)

                if not daemon:
                    break

            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

        thread = Thread(target=task)
        thread.start()

        return thread

    def _run_programs(self) -> None:
        """
        Run configured pre-run programs.
        """

        for path, prop in self.challenges:
            for program in prop.prerun_programs:
                stdout, stderr = self._parse_logger_config(program)
                thread = self._run_program(
                    program.daemon, program.cmd, stdout=stdout, stderr=stderr, cwd=path
                )
                self._threads.append(thread)

    def _stop_programs(self) -> None:
        """
        Stop running programs.
        """

        for process in self._processes:
            process.kill()

        self._threads.clear()

    def _run_entrypoint(self, entrypoint: Sequence[str]) -> None:
        """
        Run entrypoint in foreground.

        Args:
            entrypoint (Sequence[str]): The entrypoint to run.
        """

        process = subprocess.Popen(entrypoint)
        process.communicate()

        self.stop()

    def run(self, entrypoint: Sequence[str] | None = None) -> None:
        """
        Run production environment.

        Args:
            entrypoint (Sequence[str] | None, optional): If it is not None, it will be run as entrypoint in foreground. Defaults to None.
        """

        if self._running:
            raise RuntimeError("The environment is running.")

        self._running = True

        self._run_programs()

        if entrypoint is not None:
            self._run_entrypoint(entrypoint)

    def stop(self) -> None:
        """
        Stop production environment.
        """

        if not self._running:
            raise RuntimeError("The environment is not running.")

        self._running = False

        self._stop_programs()

    def __init__(
        self,
        challenges: Iterable[StrPath],
        logger: Logger,
    ) -> None:
        """
        Initialize production environment runner.

        Args:
            challenges (Iterable[StrPath]): Paths to built challenges.
            logger (Logger): The logger used in production environment.
        """

        self.challenges = [(Path(path), ProdProperty.load(path)) for path in challenges]
        self.logger = logger

        self._processes = []
        self._threads = []
        self._running = False
