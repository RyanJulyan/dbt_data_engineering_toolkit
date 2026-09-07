"""Transactional, post-sync dbt project generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

from ..adapters import AdapterRegistry
from ..brokers.datacontracts import DataContractBroker
from ..brokers.files import FileBroker
from ..brokers.projects import ProjectWorkspaceBroker
from ..errors import DataContractExecutionError, FileOperationError
from ..generation import MANIFEST, load_manifest, plan_changes, sha256_bytes
from ..models import DataProductSpecification
from ..operational import Artifact, ArtifactChange, JsonValue
from ..registry import OperatorRegistry
from ..version import COMPILER_VERSION, ODCS_VERSION, WORKBOOK_SCHEMA_VERSION

SYNC_ROOT = Path("tests/datacontract_cli")
SYNC_READABLE_STEM_LENGTH = 32
SYNC_DIGEST_LENGTH = 12


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    changes: tuple[ArtifactChange, ...]
    manifest: dict[str, JsonValue]


class ProjectGenerationService:
    """Generate, synchronize, hash, then publish without partial writes."""

    def __init__(
        self,
        *,
        files: FileBroker,
        projects: ProjectWorkspaceBroker,
        datacontract: DataContractBroker,
        registry: OperatorRegistry,
        adapters: AdapterRegistry,
    ) -> None:
        self.files = files
        self.projects = projects
        self.datacontract = datacontract
        self.registry = registry
        self.adapters = adapters

    def plan_or_publish(
        self,
        *,
        workbook: Path,
        project: Path,
        spec: DataProductSpecification,
        compiler_artifacts: list[Artifact],
        publish: bool,
        force: bool = False,
        prune: bool = False,
    ) -> GenerationPlan:
        staging = self.projects.stage(project)
        try:
            old_manifest = load_manifest(project, self.files)
            old_sync_paths = self._old_sync_paths(old_manifest)
            self.projects.delete_tree(staging / SYNC_ROOT)
            self._write_compiler_artifacts(staging, compiler_artifacts)

            contract_relative = Path("contracts") / f"{spec.metadata.product_id}.odcs.yaml"
            staged_contract = staging / contract_relative
            self._require_success(
                "Data Contract lint",
                self.datacontract.lint(staged_contract),
            )
            self._require_success(
                "Data Contract dbt sync",
                self.datacontract.dbt_sync(staged_contract, staging, dry_run=False),
            )
            self._compact_synchronized_test_paths(staging)

            synchronized = self._synchronized_artifacts(staging, compiler_artifacts)
            final_artifacts = self._post_sync_artifacts(staging, compiler_artifacts, synchronized)
            self._validate_synchronized(final_artifacts)
            changes, manifest = plan_changes(
                project,
                final_artifacts,
                force=force,
                prune=prune,
                file_broker=self.files,
            )
            self._complete_manifest(
                manifest,
                workbook=workbook,
                spec=spec,
                compiler_artifacts=compiler_artifacts,
                synchronized=synchronized,
            )
            changes.append(self._manifest_change(project, manifest))
            if publish:
                if not prune:
                    self._restore_retained_sync_files(
                        project,
                        staging,
                        old_sync_paths,
                        {item.path for item in synchronized},
                    )
                self._apply_deletions(staging, changes)
                self.files.write_text_atomic(
                    staging / MANIFEST,
                    self._manifest_text(manifest),
                )
                self.projects.publish(staging, project)
            return GenerationPlan(tuple(changes), manifest)
        finally:
            self.projects.cleanup(staging)

    @staticmethod
    def _old_sync_paths(manifest: dict[str, JsonValue]) -> set[Path]:
        raw_sources = manifest.get("managed_by")
        if not isinstance(raw_sources, dict):
            return set()
        raw = raw_sources.get("contract_sync")
        if not isinstance(raw, list):
            return set()
        return {Path(str(item)) for item in raw}

    def _write_compiler_artifacts(self, staging: Path, artifacts: list[Artifact]) -> None:
        for artifact in artifacts:
            self.files.write_text_atomic(staging / artifact.path, artifact.content)

    @staticmethod
    def _require_success(label: str, result: object) -> None:
        succeeded = bool(getattr(result, "succeeded", False))
        if succeeded:
            return
        output = str(getattr(result, "output", "")).strip()
        command = tuple(str(item) for item in getattr(result, "command", ()))
        return_code = getattr(result, "return_code", None)
        message = f"{label} failed in staging; the existing project was not changed."
        if output:
            message += f"\n{output}"
        raise DataContractExecutionError(
            "datacontract",
            message,
            command=command,
            return_code=return_code if isinstance(return_code, int) else None,
        )

    def _synchronized_artifacts(
        self,
        staging: Path,
        compiler_artifacts: list[Artifact],
    ) -> list[Artifact]:
        root = staging / SYNC_ROOT
        artifacts: dict[Path, Artifact] = {}
        for path in self.projects.list_files(root):
            relative = path.relative_to(staging)
            artifacts[relative] = Artifact(relative, self.files.read_text(path))
        for emitted in compiler_artifacts:
            synchronized_content = self.files.read_text(staging / emitted.path)
            if synchronized_content != emitted.content:
                artifacts[emitted.path] = Artifact(emitted.path, synchronized_content)
        return [artifacts[path] for path in sorted(artifacts)]

    def _compact_synchronized_test_paths(self, staging: Path) -> None:
        """Flatten dependency-generated tests into deterministic Windows-safe paths."""

        root = staging / SYNC_ROOT
        original_paths = self.projects.list_files(root)
        if not original_paths:
            return

        compacted: dict[Path, str] = {}
        for original in original_paths:
            relative = original.relative_to(root)
            compact_path = self._compact_sync_path(relative)
            if compact_path in compacted:
                raise DataContractExecutionError(
                    "datacontract",
                    f"Data Contract dbt sync produced colliding test paths at {compact_path}.",
                )
            compacted[compact_path] = self.files.read_text(original)

        self.projects.delete_tree(root)
        for relative, content in sorted(compacted.items()):
            self.files.write_text_atomic(staging / relative, content)

    @staticmethod
    def _compact_sync_path(relative: Path) -> Path:
        source = relative.as_posix()
        digest = sha256_bytes(source.encode("utf-8"))[:SYNC_DIGEST_LENGTH]
        pieces = relative.stem.split("__")
        readable_source = "__".join(pieces[-2:]) if len(pieces) >= 2 else relative.stem
        readable = "".join(
            character if character.isalnum() or character == "_" else "_"
            for character in readable_source
        )
        readable = readable.strip("_")[:SYNC_READABLE_STEM_LENGTH].rstrip("_") or "test"
        suffix = relative.suffix.casefold() or ".sql"
        return SYNC_ROOT / f"dc_{readable}__{digest}{suffix}"

    @staticmethod
    def _validate_synchronized(artifacts: list[Artifact]) -> None:
        yaml_artifacts = [
            item
            for item in artifacts
            if item.path.suffix.casefold() in {".yml", ".yaml"}
            and item.path.parts
            and item.path.parts[0] == "models"
        ]
        if not yaml_artifacts:
            raise DataContractExecutionError(
                "datacontract",
                "The staged project contains no dbt model schema YAML to validate after Data "
                "Contract sync; the existing project was not changed.",
            )
        for artifact in yaml_artifacts:
            try:
                payload = yaml.safe_load(artifact.content)
            except yaml.YAMLError as exc:
                raise DataContractExecutionError(
                    "datacontract",
                    f"Data Contract dbt sync produced invalid YAML at {artifact.path}: {exc}",
                ) from exc
            if not isinstance(payload, dict) or int(payload.get("version", 0)) != 2:
                raise DataContractExecutionError(
                    "datacontract",
                    f"Data Contract dbt sync produced an invalid dbt schema document at "
                    f"{artifact.path}; expected a top-level version: 2.",
                )

    def _post_sync_artifacts(
        self,
        staging: Path,
        compiler_artifacts: list[Artifact],
        synchronized: list[Artifact],
    ) -> list[Artifact]:
        paths = {item.path for item in compiler_artifacts}
        paths.update(item.path for item in synchronized)
        return [Artifact(path, self.files.read_text(staging / path)) for path in sorted(paths)]

    def _complete_manifest(
        self,
        manifest: dict[str, JsonValue],
        *,
        workbook: Path,
        spec: DataProductSpecification,
        compiler_artifacts: list[Artifact],
        synchronized: list[Artifact],
    ) -> None:
        compiler_paths = cast(
            list[JsonValue],
            sorted(item.path.as_posix() for item in compiler_artifacts),
        )
        sync_paths = cast(
            list[JsonValue],
            sorted(item.path.as_posix() for item in synchronized),
        )
        managed_by: dict[str, JsonValue] = {
            "compiler": compiler_paths,
            "contract_sync": sync_paths,
        }
        metadata: dict[str, JsonValue] = {
            "compiler_version": COMPILER_VERSION,
            "workbook_schema_version": WORKBOOK_SCHEMA_VERSION,
            "workbook_sha256": sha256_bytes(self.files.read_bytes(workbook)),
            "operator_registry_sha256": self.registry.fingerprint(),
            "odcs_version": ODCS_VERSION,
            "adapter": spec.build.adapter,
            "dbt_adapter_dependency": self._adapter_dependency(spec.build.adapter),
            "contract_authority": spec.build.contract_test_authority,
            "managed_by": managed_by,
        }
        manifest.update(metadata)

    def _adapter_dependency(self, adapter: str) -> str:
        provider = self.adapters.get(adapter)
        return provider.dbt_dependency if provider else "unsupported"

    @staticmethod
    def _manifest_text(manifest: dict[str, JsonValue]) -> str:
        return json.dumps(manifest, indent=2, sort_keys=True) + "\n"

    def _manifest_change(
        self,
        project: Path,
        manifest: dict[str, JsonValue],
    ) -> ArtifactChange:
        path = project / MANIFEST
        if not self.files.exists(path):
            return ArtifactChange("create", Path(MANIFEST))
        current = self.files.read_text(path)
        action = "unchanged" if current == self._manifest_text(manifest) else "update"
        return ArtifactChange(action, Path(MANIFEST))

    def _restore_retained_sync_files(
        self,
        project: Path,
        staging: Path,
        previous: set[Path],
        current: set[Path],
    ) -> None:
        for relative in sorted(previous - current):
            if not relative.is_relative_to(SYNC_ROOT):
                continue
            source = project / relative
            if self.files.exists(source):
                self.projects.copy_file(source, staging / relative)

    def _apply_deletions(self, staging: Path, changes: list[ArtifactChange]) -> None:
        for change in changes:
            if change.action != "delete":
                continue
            path = staging / change.path
            if not self.files.exists(path):
                continue
            try:
                self.files.delete(path)
            except FileOperationError:
                raise
