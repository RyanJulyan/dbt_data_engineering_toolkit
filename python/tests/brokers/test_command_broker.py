"""Executable discovery stays anchored to the active Python environment."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dbt_data_engineering_toolkit_compiler.brokers.commands import SubprocessCommandBroker
from dbt_data_engineering_toolkit_compiler.brokers.datacontracts import (
    CliDataContractBroker,
)
from dbt_data_engineering_toolkit_compiler.operational import CommandResult


class RecordingCommands:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], Path | None]] = []

    def find(self, executable: str) -> str | None:
        return f"/active/bin/{executable}"

    def run(self, command, *, cwd: Path | None = None) -> CommandResult:
        arguments = tuple(command)
        self.calls.append((arguments, cwd))
        return CommandResult(arguments, 0)


class CommandBrokerTests(unittest.TestCase):
    def test_finds_dependency_installed_beside_running_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = Path(temporary)
            python = environment / "python"
            executable = environment / "dbt"
            executable.touch()

            with patch(
                "dbt_data_engineering_toolkit_compiler.brokers.commands.sys.executable",
                str(python),
            ):
                found = SubprocessCommandBroker().find("dbt")

            self.assertEqual(found, str(executable))

    def test_datacontract_excel_commands_use_official_cli_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = RecordingCommands()
            broker = CliDataContractBroker(commands)
            source = root / "contracts" / "standard_odcs.xlsx"
            canonical = root / "work" / "canonical.odcs.yaml"
            exported = root / "work" / "standard_odcs.xlsx"

            broker.import_excel(source, canonical)
            broker.export_excel(canonical, exported)

            self.assertEqual(
                commands.calls,
                [
                    (
                        (
                            "/active/bin/datacontract",
                            "import",
                            "excel",
                            "--source",
                            str(source),
                            "--output",
                            str(canonical),
                        ),
                        source.parent,
                    ),
                    (
                        (
                            "/active/bin/datacontract",
                            "export",
                            "excel",
                            str(canonical),
                            "--output",
                            str(exported),
                        ),
                        canonical.parent,
                    ),
                ],
            )


if __name__ == "__main__":
    unittest.main()
