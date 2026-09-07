"""Broker for executable discovery and subprocess execution."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Protocol

from ..operational import CommandResult


class CommandBroker(Protocol):
    """External command boundary consumed by dependency-specific brokers."""

    def find(self, executable: str) -> str | None: ...

    def run(self, command: Iterable[str], *, cwd: Path | None = None) -> CommandResult: ...


class SubprocessCommandBroker:
    """Production command broker backed by the operating system."""

    def find(self, executable: str) -> str | None:
        suffix = ".exe" if sys.platform == "win32" else ""
        sibling = Path(sys.executable).parent / f"{executable}{suffix}"
        if sibling.is_file():
            return str(sibling)
        return shutil.which(executable)

    def run(self, command: Iterable[str], *, cwd: Path | None = None) -> CommandResult:
        arguments = tuple(str(item) for item in command)
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(
            command=arguments,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
