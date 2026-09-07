"""Dependency-specific brokers built on the shared command boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..errors import MissingDependencyError
from ..operational import CommandResult
from .commands import CommandBroker, SubprocessCommandBroker


class DbtBroker(Protocol):
    def parse(self, project: Path) -> CommandResult: ...

    def seed(
        self, project: Path, *, selector: str | None = None, exclude: str | None = None
    ) -> CommandResult: ...

    def build(self, project: Path, *, exclude: str | None = None) -> CommandResult: ...

    def run(self, project: Path, *, selector: str | None = None) -> CommandResult: ...

    def deps(self, project: Path) -> CommandResult: ...


class CliDbtBroker:
    def __init__(self, commands: CommandBroker | None = None) -> None:
        self.commands = commands or SubprocessCommandBroker()

    def _dbt(self) -> str:
        executable = self.commands.find("dbt")
        if not executable:
            raise MissingDependencyError(
                "dbt", "dbt is not installed; install the compiler and target adapter."
            )
        return executable

    def _run(self, project: Path, operation: str, *arguments: str) -> CommandResult:
        return self.commands.run(
            (
                self._dbt(),
                operation,
                "--project-dir",
                str(project),
                "--profiles-dir",
                str(project),
                *arguments,
            ),
            cwd=project,
        )

    def parse(self, project: Path) -> CommandResult:
        return self._run(project, "parse")

    def seed(
        self, project: Path, *, selector: str | None = None, exclude: str | None = None
    ) -> CommandResult:
        arguments: list[str] = []
        if selector:
            arguments.extend(("--select", selector))
        if exclude:
            arguments.extend(("--exclude", exclude))
        return self._run(project, "seed", *arguments)

    def build(self, project: Path, *, exclude: str | None = None) -> CommandResult:
        arguments = ("--exclude", exclude) if exclude else ()
        return self._run(project, "build", *arguments)

    def run(self, project: Path, *, selector: str | None = None) -> CommandResult:
        arguments = ("--select", selector) if selector else ()
        return self._run(project, "run", *arguments)

    def deps(self, project: Path) -> CommandResult:
        return self._run(project, "deps")


class SqlFluffBroker(Protocol):
    def lint(self, project: Path) -> CommandResult: ...


class CliSqlFluffBroker:
    def __init__(self, commands: CommandBroker | None = None) -> None:
        self.commands = commands or SubprocessCommandBroker()

    def lint(self, project: Path) -> CommandResult:
        executable = self.commands.find("sqlfluff")
        if not executable:
            raise MissingDependencyError(
                "sqlfluff", "sqlfluff is not installed; reinstall the compiler."
            )
        config = project / ".sqlfluff"
        targets = tuple(name for name in ("models", "tests") if (project / name).exists())
        return self.commands.run(
            (executable, "lint", *targets, "--config", str(config)),
            cwd=project,
        )
