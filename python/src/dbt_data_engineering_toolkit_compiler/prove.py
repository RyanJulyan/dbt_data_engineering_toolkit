"""Isolated end-to-end proof service for a generated data product."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from .brokers.datacontracts import CliDataContractBroker, DataContractBroker
from .brokers.dependencies import (
    CliDbtBroker,
    CliSqlFluffBroker,
    DbtBroker,
    SqlFluffBroker,
)
from .brokers.files import FileBroker, LocalFileBroker
from .errors import MissingDependencyError
from .operational import CommandResult

IGNORED_PROJECT_NAMES = {
    ".det",
    ".det-manifest.json",
    "dbt_packages",
    "logs",
    "target",
}
EVALUATOR_SELECTOR = "package:dbt_project_evaluator"


class ProjectProofService:
    """Orchestrate dependency brokers without leaking commands into the CLI."""

    def __init__(
        self,
        *,
        files: FileBroker | None = None,
        dbt: DbtBroker | None = None,
        sqlfluff: SqlFluffBroker | None = None,
        datacontract: DataContractBroker | None = None,
    ) -> None:
        self.files = files or LocalFileBroker()
        self.dbt = dbt or CliDbtBroker()
        self.sqlfluff = sqlfluff or CliSqlFluffBroker()
        self.datacontract = datacontract or CliDataContractBroker()

    def prove(
        self,
        project: Path,
        contract_relative_path: Path,
        *,
        run_evaluator: bool = True,
        local_package_root: Path | None = None,
    ) -> tuple[bool, list[str]]:
        messages: list[str] = []
        try:
            contract_result = self.datacontract.lint(project / contract_relative_path)
            if not self._record(messages, "Data Contract lint", contract_result):
                return False, messages

            with tempfile.TemporaryDirectory(
                prefix=f".{project.name}-det-prove-", dir=project.parent
            ) as temporary:
                proof_project = Path(temporary)
                self.files.copy_tree(
                    project,
                    proof_project,
                    IGNORED_PROJECT_NAMES,
                )
                if local_package_root is not None:
                    self._use_local_packages(proof_project, local_package_root)
                proof_contract = proof_project / contract_relative_path

                if not self._record(
                    messages,
                    "dbt dependencies",
                    self.dbt.deps(proof_project),
                ):
                    return False, messages
                if not self._record(
                    messages,
                    "Data Contract dbt sync",
                    self.datacontract.dbt_sync(
                        proof_contract,
                        proof_project,
                        dry_run=False,
                    ),
                ):
                    return False, messages
                if not self._record(
                    messages,
                    "SQLFluff dbt lint",
                    self.sqlfluff.lint(proof_project),
                ):
                    return False, messages
                if not self._record(
                    messages,
                    "dbt parse",
                    self.dbt.parse(proof_project),
                ):
                    return False, messages
                if not self._record(
                    messages,
                    "dbt source seeds",
                    self.dbt.seed(
                        proof_project,
                        exclude=EVALUATOR_SELECTOR,
                    ),
                ):
                    return False, messages
                if not self._record(
                    messages,
                    "dbt build",
                    self.dbt.build(
                        proof_project,
                        exclude=EVALUATOR_SELECTOR,
                    ),
                ):
                    return False, messages
                if run_evaluator:
                    if not self._record(
                        messages,
                        "dbt_project_evaluator seed",
                        self.dbt.seed(
                            proof_project,
                            selector=EVALUATOR_SELECTOR,
                        ),
                    ):
                        return False, messages
                    if not self._record(
                        messages,
                        "dbt_project_evaluator run",
                        self._run_evaluator(proof_project),
                    ):
                        return False, messages
        except MissingDependencyError as exc:
            messages.append(str(exc))
            return False, messages
        return True, messages

    def _run_evaluator(self, project: Path) -> CommandResult:
        # Evaluator models run through dbt's normal run operation. The protocol keeps
        # only the commands required by services, so this capability is explicit.
        run = getattr(self.dbt, "run", None)
        if run is None:
            return CommandResult(
                command=("dbt", "run"),
                return_code=2,
                stderr="Configured dbt broker does not implement run().",
            )
        return run(project, selector=EVALUATOR_SELECTOR)

    def _use_local_packages(self, project: Path, package_root: Path) -> None:
        root = package_root.resolve()
        canonical = root / "dbt" if (root / "dbt" / "dbt_project.yml").exists() else root
        alias = (
            root / "aliases" / "de_toolkit"
            if (root / "aliases" / "de_toolkit" / "dbt_project.yml").exists()
            else root / "aliases" / "de_toolkit"
        )
        payload = {
            "packages": [
                {"local": str(canonical)},
                {"local": str(alias)},
            ]
        }
        self.files.write_text_atomic(
            project / "packages.yml",
            yaml.safe_dump(payload, sort_keys=False),
        )

    @staticmethod
    def _record(messages: list[str], label: str, result: CommandResult) -> bool:
        state = "passed" if result.succeeded else "failed"
        messages.append(f"{label}: {state}\n{result.output}".rstrip())
        return result.succeeded
