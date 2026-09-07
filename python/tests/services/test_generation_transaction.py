"""Acceptance coverage for post-sync transactional publication."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from dbt_data_engineering_toolkit_compiler.adapters import AdapterRegistry
from dbt_data_engineering_toolkit_compiler.brokers.files import LocalFileBroker
from dbt_data_engineering_toolkit_compiler.brokers.projects import LocalProjectWorkspaceBroker
from dbt_data_engineering_toolkit_compiler.errors import DataContractExecutionError
from dbt_data_engineering_toolkit_compiler.generation import sha256_bytes
from dbt_data_engineering_toolkit_compiler.operational import ArtifactChange, CommandResult
from dbt_data_engineering_toolkit_compiler.registry import OperatorRegistry
from dbt_data_engineering_toolkit_compiler.services.emissions.service import EmissionService
from dbt_data_engineering_toolkit_compiler.services.generation import ProjectGenerationService
from dbt_data_engineering_toolkit_compiler.services.workbooks.service import (
    WorkbookInterpretationService,
)


class SuccessfulContractBroker:
    def lint(self, contract: Path) -> CommandResult:
        return CommandResult(("datacontract", "lint", str(contract)), 0, "valid")

    def dbt_sync(self, contract: Path, project: Path, *, dry_run: bool) -> CommandResult:
        del contract, dry_run
        generated = project / (
            "tests/datacontract_cli/urn_datacontract_customer_customer_360/"
            "urn_datacontract_customer_customer_360__1_0_0__stg_customers__"
            "the_published_customer_product_must_contain_rows.sql"
        )
        generated.parent.mkdir(parents=True, exist_ok=True)
        generated.write_text("select 1 where false\n", encoding="utf-8")
        return CommandResult(("datacontract", "dbt", "sync"), 0, "synchronized")


class FailingContractBroker(SuccessfulContractBroker):
    def dbt_sync(self, contract: Path, project: Path, *, dry_run: bool) -> CommandResult:
        del contract, project, dry_run
        return CommandResult(("datacontract", "dbt", "sync"), 1, stderr="sync failed")


def _service(contract: object, registry: OperatorRegistry) -> ProjectGenerationService:
    return ProjectGenerationService(
        files=LocalFileBroker(),
        projects=LocalProjectWorkspaceBroker(),
        datacontract=contract,  # type: ignore[arg-type]
        registry=registry,
        adapters=AdapterRegistry.default(),
    )


def _workbook() -> Path:
    return Path(
        str(
            files("dbt_data_engineering_toolkit_compiler")
            / "resources"
            / "data_product_sample.xlsx"
        )
    )


def test_sync_failure_leaves_existing_destination_untouched(tmp_path: Path) -> None:
    workbook = _workbook()
    spec = WorkbookInterpretationService().load(workbook)
    registry = OperatorRegistry.load()
    project = tmp_path / "project"
    project.mkdir()
    marker = project / "existing.txt"
    marker.write_text("unchanged\n", encoding="utf-8")
    runtime_cache = project / "target" / "manifest.json"
    runtime_cache.parent.mkdir()
    runtime_cache.write_text("{}\n", encoding="utf-8")

    try:
        _service(FailingContractBroker(), registry).plan_or_publish(
            workbook=workbook,
            project=project,
            spec=spec,
            compiler_artifacts=EmissionService(registry=registry).emit_all(spec),
            publish=True,
            prune=True,
        )
    except DataContractExecutionError as exc:
        assert "existing project was not changed" in str(exc)
    else:
        raise AssertionError("expected staged contract sync to fail")

    assert marker.read_text(encoding="utf-8") == "unchanged\n"
    assert runtime_cache.read_text(encoding="utf-8") == "{}\n"
    assert not (project / "dbt_project.yml").exists()
    assert not (project / ".det-manifest.json").exists()


def test_manifest_hashes_post_sync_output_and_second_plan_is_clean(tmp_path: Path) -> None:
    workbook = _workbook()
    spec = WorkbookInterpretationService().load(workbook)
    registry = OperatorRegistry.load()
    project = tmp_path / "project"
    service = _service(SuccessfulContractBroker(), registry)
    artifacts = EmissionService(registry=registry).emit_all(spec)

    first = service.plan_or_publish(
        workbook=workbook,
        project=project,
        spec=spec,
        compiler_artifacts=artifacts,
        publish=True,
        prune=True,
    )
    assert any(item.action == "create" for item in first.changes)

    manifest = json.loads((project / ".det-manifest.json").read_text(encoding="utf-8"))
    synchronized_files = list((project / "tests/datacontract_cli").glob("dc_*.sql"))
    assert len(synchronized_files) == 1
    synchronized = synchronized_files[0]
    relative = synchronized.relative_to(project).as_posix()
    assert synchronized.parent == project / "tests/datacontract_cli"
    assert len(relative) <= 80
    assert "urn_datacontract" not in relative
    assert manifest["files"][relative] == sha256_bytes(synchronized.read_bytes())
    assert relative in manifest["managed_by"]["contract_sync"]

    second = service.plan_or_publish(
        workbook=workbook,
        project=project,
        spec=spec,
        compiler_artifacts=artifacts,
        publish=False,
        prune=True,
    )
    assert all(item.action == "unchanged" for item in second.changes)

    changed_workbook = tmp_path / "changed-workbook.xlsx"
    changed_workbook.write_bytes(workbook.read_bytes() + b"\n")
    workbook_only = service.plan_or_publish(
        workbook=changed_workbook,
        project=project,
        spec=spec,
        compiler_artifacts=artifacts,
        publish=False,
        prune=True,
    )
    assert ArtifactChange("update", Path(".det-manifest.json")) in workbook_only.changes
