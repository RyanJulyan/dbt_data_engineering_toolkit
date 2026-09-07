"""Focused tests for independent artifact-emitter composition."""

from pathlib import Path

from dbt_data_engineering_toolkit_compiler.models import (
    DataProductSpecification,
    ProductMetadata,
)
from dbt_data_engineering_toolkit_compiler.operational import Artifact
from dbt_data_engineering_toolkit_compiler.services.emissions.service import EmissionService


class StubEmitter:
    def __init__(self, path: str) -> None:
        self.path = path

    def emit(self, specification: DataProductSpecification) -> list[Artifact]:
        return [Artifact(Path(self.path), specification.metadata.product_id)]


def test_emit_all_composes_contract_and_project_artifacts() -> None:
    specification = DataProductSpecification(
        metadata=ProductMetadata(product_id="product", name="Product")
    )
    service = EmissionService(
        contracts=StubEmitter("contracts/product.odcs.yaml"),
        dbt_project=StubEmitter("dbt_project.yml"),
    )

    assert [item.path.as_posix() for item in service.emit_all(specification)] == [
        "contracts/product.odcs.yaml",
        "dbt_project.yml",
    ]
