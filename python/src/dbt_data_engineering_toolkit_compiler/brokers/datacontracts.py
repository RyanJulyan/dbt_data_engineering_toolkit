"""Broker for the authoritative Data Contract CLI and Python API."""
# pyright: reportMissingImports=false

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..errors import MissingDependencyError
from ..operational import CommandResult
from .commands import CommandBroker, SubprocessCommandBroker


class DataContractBroker(Protocol):
    def lint(self, contract: Path) -> CommandResult: ...

    def dbt_sync(self, contract: Path, project: Path, *, dry_run: bool) -> CommandResult: ...

    def import_excel(self, workbook: Path, output: Path) -> CommandResult: ...

    def export_excel(self, contract: Path, output: Path) -> CommandResult: ...


class CliDataContractBroker:
    """Production Data Contract integration behind a local interface."""

    def __init__(self, commands: CommandBroker | None = None) -> None:
        self.commands = commands or SubprocessCommandBroker()

    def lint(self, contract: Path) -> CommandResult:
        try:
            from datacontract.data_contract import DataContract
        except ModuleNotFoundError as exc:
            raise MissingDependencyError(
                "datacontract",
                "Data Contract CLI is missing; reinstall the compiler.",
            ) from exc
        result = DataContract(data_contract_file=str(contract)).lint()
        return CommandResult(
            command=("datacontract", "lint", str(contract)),
            return_code=0 if result.has_passed() else 1,
            stdout=str(result),
        )

    def dbt_sync(self, contract: Path, project: Path, *, dry_run: bool) -> CommandResult:
        executable = self._executable()
        command = [
            executable,
            "dbt",
            "sync",
            str(contract),
            "--project-dir",
            str(project),
        ]
        if dry_run:
            command.append("--dry-run")
        return self.commands.run(command, cwd=project)

    def import_excel(self, workbook: Path, output: Path) -> CommandResult:
        """Convert an official ODCS workbook with Data Contract CLI."""

        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self._executable(),
            "import",
            "excel",
            "--source",
            str(workbook),
            "--output",
            str(output),
        ]
        return self.commands.run(command, cwd=workbook.parent)

    def export_excel(self, contract: Path, output: Path) -> CommandResult:
        """Export canonical ODCS YAML using Data Contract CLI's official template."""

        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self._executable(),
            "export",
            "excel",
            str(contract),
            "--output",
            str(output),
        ]
        return self.commands.run(command, cwd=contract.parent)

    def _executable(self) -> str:
        executable = self.commands.find("datacontract")
        if executable:
            return executable
        raise MissingDependencyError(
            "datacontract",
            "Data Contract CLI is missing; reinstall the compiler.",
        )
