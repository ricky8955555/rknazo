"""
Providing CLI.
"""

import curses
import os
from argparse import ArgumentParser

from rknazo.anura.exc import ValidationFailed
from rknazo.anura.flag import ValidatableFlag
from rknazo.anura.utils import (
    decrypt_flags,
    make_uuid_like_flag,
    unwrap_flag,
    validate_uuid_like_flag,
)


class Interactive:
    """
    Providing interactive CLI for user.
    """

    stdscr: curses.window
    """
    The curses window to output.
    """

    file: str
    """
    The file to store the flags.
    """

    def __init__(self, stdscr: curses.window, file: str) -> None:
        """
        Initialize the interactive CLI.

        Args:
            file (str): The file to store the flags.
        """

        self.file = file
        self.stdscr = stdscr

    def _load_flags(self) -> list[ValidatableFlag]:
        """
        Load flags from file.

        Returns:
            list[ValidatableFlag]: The validated flags loaded from file.
        """

        if not os.path.exists(self.file):
            return []

        with open(self.file, "r") as fp:
            lines = fp.read().splitlines()

        flags = list(map(validate_uuid_like_flag, lines))
        return flags

    def _write_flags(self, flags: list[ValidatableFlag]) -> None:
        """
        Write flags to file. (Overwritten)

        Args:
            flags (list[ValidatableFlag]): The validated flags written to the file.
        """

        lines = list(map(make_uuid_like_flag, flags))

        with open(self.file, "w") as fp:
            fp.write("\n".join(lines))

    def decrypt(self) -> None:
        """
        Interactively decrypt flags saved in file.
        """

        flags = self._load_flags()

        if not flags:
            return self.stdscr.addstr("|- You've done none of the challenges. XD\n")

        try:
            results = decrypt_flags(flags)
        except ValidationFailed as ex:
            self.stdscr.addstr(
                "|- Decrypt flags failed. Probably because you've not done all the challenges.\n"
            )
            self.stdscr.addstr(f"|- Reason: {ex}\n")
            return

        result = b"".join(results)
        self.stdscr.addstr(f"|- Hooray! Here is something you want: {result}\n")

    def add_flag(self) -> None:
        """
        Interactively add flag from user input.
        """

        self.stdscr.addstr("Please type your flag: ")
        flag = self.stdscr.getstr().decode().strip()

        try:
            flag = unwrap_flag(flag)
        except ValueError as ex:
            self.stdscr.addstr("|- The flag is not valid.\n")
            self.stdscr.addstr(f"|- Reason: {ex}\n")
            return
        except ValidationFailed as ex:
            self.stdscr.addstr("|- Validation for the flag is failed.\n")
            self.stdscr.addstr(f"|- Reason: {ex}\n")
            return

        flags = self._load_flags()
        solved = next(
            iter(cur for cur in flags if cur.challenge_id == flag.challenge_id),
            None,
        )

        if solved is not None:
            if flag == solved:
                return self.stdscr.addstr("|- You've previously solved this challenge.\n")
            self.stdscr.addstr(
                "|- You've previously solved a challenge with same ID but different data.\n"
            )
            self.stdscr.addstr("Confirm to replace it? (Y/n) ")
            confirm = self.stdscr.getstr().lower() in [b"", b"y"]
            if not confirm:
                return self.stdscr.addstr("|- The process was cancelled.\n")
            flags.remove(solved)
            self.stdscr.addstr("|- The old flag is removed and being replaced by the new one.\n")

        flags.append(flag)
        self._write_flags(flags)

        self.stdscr.addstr(f"|- Cheers! You've passed the challenge {flag.challenge_id}.\n")

    def show_progress(self) -> None:
        """
        Interactively show the progress.
        """

        flags = self._load_flags()

        if not flags:
            return self.stdscr.addstr("|- You've done none of the challenges. XD\n")

        solved = ", ".join(str(flag.challenge_id) for flag in flags)
        self.stdscr.addstr(f"|- The challenge you've solved: {solved} ({len(flags)} in total).\n")

    def select(self) -> bool:
        """
        Interactively provide choice for user to select.

        Returns:
            bool: If it is False, indicating that the program needs to exit.
        """

        self.stdscr.addstr("Choose the operation by index:\n")
        self.stdscr.addstr("|- 1. Add and check a flag\n")
        self.stdscr.addstr("|- 2. Decrypt flags\n")
        self.stdscr.addstr("|- 3. Show current progress\n")
        self.stdscr.addstr("|- 0. Exit\n")

        self.stdscr.addstr("Choice: ")

        entries = [self.add_flag, self.decrypt, self.show_progress]

        inp = self.stdscr.getstr()
        self.stdscr.clear()

        try:
            choice = int(inp)
            if choice < 0 or choice > len(entries):
                raise ValueError
        except ValueError:
            self.stdscr.addstr("|- You've typed an invalid choice~\n")
            return True

        if choice == 0:
            return False

        entries[choice - 1]()

        return True

    def entry(self) -> None:
        """
        The entry of interactive CLI.
        """

        while True:
            self.stdscr.clear()

            try:
                if not self.select():
                    break
            except KeyboardInterrupt:
                break
            except Exception as ex:
                self.stdscr.addstr(f"Some unexpected error happened: {ex}\n")

            self.stdscr.addstr("Press any key to continue... ")
            self.stdscr.getkey()


def main() -> None:
    """
    The entry of the CLI program.
    """

    parser = ArgumentParser()
    parser.add_argument(
        "--file",
        "-f",
        help=(
            "select the file to store the flags. "
            "Default: 'flags' file in current working directory."
        ),
    )
    args = parser.parse_args()

    stdscr = curses.initscr()
    flags = os.path.abspath(args.file or "flags")

    interactive = Interactive(stdscr, flags)
    interactive.entry()

    curses.endwin()


if __name__ == "__main__":
    main()
