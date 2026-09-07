"""Top-level emission service composing contract and dbt project emitters."""

from __future__ import annotations

from typing import Protocol

from ...adapters import AdapterRegistry
from ...models import DataProductSpecification
from ...operational import Artifact
from ...registry import OperatorRegistry
from .contracts import ContractEmitter
from .project import DbtProjectEmitter
from .project_config import ProjectConfigurationEmitter


class ArtifactEmitter(Protocol):
    def emit(self, spec: DataProductSpecification) -> list[Artifact]: ...


class EmissionService:
    def __init__(
        self,
        contracts: ArtifactEmitter | None = None,
        dbt_project: ArtifactEmitter | None = None,
        registry: OperatorRegistry | None = None,
        adapters: AdapterRegistry | None = None,
    ) -> None:
        self.contracts = contracts or ContractEmitter()
        self.dbt_project = dbt_project or DbtProjectEmitter(
            registry=registry,
            configuration=ProjectConfigurationEmitter(adapters),
        )

    def emit_contracts(self, spec: DataProductSpecification) -> list[Artifact]:
        return self.contracts.emit(spec)

    def emit_dbt_project(self, spec: DataProductSpecification) -> list[Artifact]:
        return self.dbt_project.emit(spec)

    def emit_all(self, spec: DataProductSpecification) -> list[Artifact]:
        return [*self.emit_contracts(spec), *self.emit_dbt_project(spec)]
