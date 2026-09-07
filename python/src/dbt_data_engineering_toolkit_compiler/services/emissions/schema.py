"""dbt source and model-property YAML emission."""

from __future__ import annotations

from collections import defaultdict

from ...adapters import AdapterRegistry
from ...models import (
    Cardinality,
    DataProductSpecification,
    FailureMode,
    ModelSpecification,
    SourceSpecification,
    ValidationRule,
)
from ...registry import OperatorRegistry
from .common import GENERATED_HEADER_YAML, remove_empty, yaml_text


def assertion_config(rule: ValidationRule) -> dict[str, object]:
    return {
        "description": rule.description or rule.name.replace("_", " ").title(),
        "expression": f"_{rule.name}_valid",
        "null_as_exception": True,
    }


def dbt_data_type(logical_type: str, physical_type: str | None, adapter: str) -> str:
    provider = AdapterRegistry.default().get(adapter)
    if provider is None:
        return physical_type or logical_type.casefold()
    return provider.data_type(logical_type, physical_type)


def cardinality_unique_keys(
    spec: DataProductSpecification,
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for relationship in spec.relationships:
        if relationship.cardinality in {
            Cardinality.ONE_TO_ONE,
            Cardinality.ONE_TO_MANY,
        }:
            keys.add((relationship.left_relation, relationship.left_key))
        if relationship.cardinality in {
            Cardinality.ONE_TO_ONE,
            Cardinality.MANY_TO_ONE,
        }:
            keys.add((relationship.right_relation, relationship.right_key))
    return keys


class SourceYamlEmitter:
    def emit(self, spec: DataProductSpecification) -> str:
        keys = cardinality_unique_keys(spec)
        by_source: dict[str, list[SourceSpecification]] = defaultdict(list)
        for source in spec.sources:
            by_source[source.source_name].append(source)
        payload = {
            "version": 2,
            "sources": [
                {
                    "name": source_name,
                    "database": items[0].database,
                    "schema": items[0].schema_name or "{{ target.schema }}",
                    "tables": [self._table(spec, item, keys) for item in items],
                }
                for source_name, items in sorted(by_source.items())
            ],
        }
        return GENERATED_HEADER_YAML + yaml_text(remove_empty(payload))

    @staticmethod
    def _table(
        spec: DataProductSpecification,
        source: SourceSpecification,
        keys: set[tuple[str, str]],
    ) -> dict[str, object]:
        columns: list[object] = []
        for column in spec.source_columns:
            if column.relation != source.relation:
                continue
            tests = ["unique"] if (source.relation, column.name) in keys else []
            columns.append(
                remove_empty(
                    {
                        "name": column.name,
                        "description": column.description,
                        "data_type": column.physical_type,
                        "data_tests": tests,
                    }
                )
            )
        result = remove_empty(
            {
                "name": source.table_name,
                "identifier": source.table_name,
                "description": source.description,
                "columns": columns,
            }
        )
        assert isinstance(result, dict)
        return result


class ModelYamlEmitter:
    def emit(
        self,
        spec: DataProductSpecification,
        model: ModelSpecification,
        registry: OperatorRegistry,
    ) -> str:
        del registry  # retained in the API for symmetrical emitter composition
        properties = [item for item in spec.schema_properties if item.object_name == model.name]
        rules = [item for item in spec.rules if item.model == model.name]
        reject_rules = [item for item in rules if item.failure == FailureMode.REJECT]
        warning_rules = [item for item in rules if item.failure == FailureMode.WARN]
        provider = AdapterRegistry.default().get(spec.build.adapter)
        keys = cardinality_unique_keys(spec)
        columns: list[dict[str, object]] = []
        for prop in properties:
            tests = ["unique"] if (model.name, prop.name) in keys else []
            column = remove_empty(
                {
                    "name": prop.name,
                    "description": prop.description,
                    "data_type": (
                        dbt_data_type(
                            prop.logical_type,
                            prop.physical_type,
                            spec.build.adapter,
                        )
                        if model.enforce_contract
                        else None
                    ),
                    "data_tests": tests,
                }
            )
            assert isinstance(column, dict)
            columns.append(column)
        if reject_rules:
            self._attach_assertions(
                columns,
                "_det_rejections",
                "Reject-row rule IDs that failed for this record.",
                reject_rules,
                enforce_contract=model.enforce_contract,
                data_type=(provider.operational_type("_det_rejections") if provider else "varchar"),
            )
        if warning_rules:
            self._attach_assertions(
                columns,
                "_det_warnings",
                "Warning rule IDs that failed for this record.",
                warning_rules,
                enforce_contract=model.enforce_contract,
                data_type=(provider.operational_type("_det_warnings") if provider else "varchar"),
            )
        payload = {
            "version": 2,
            "models": [
                {
                    "name": model.name,
                    "description": model.description,
                    "config": {"contract": {"enforced": model.enforce_contract}},
                    "columns": columns,
                }
            ],
        }
        return GENERATED_HEADER_YAML + yaml_text(remove_empty(payload))

    @staticmethod
    def _attach_assertions(
        columns: list[dict[str, object]],
        name: str,
        description: str,
        rules: list[ValidationRule],
        *,
        enforce_contract: bool,
        data_type: str,
    ) -> None:
        column: dict[str, object] | None = next(
            (item for item in columns if item.get("name") == name), None
        )
        if column is None:
            column = {"name": name, "description": description}
            columns.append(column)
        if enforce_contract:
            column["data_type"] = data_type
        assertions: dict[str, object] = {item.name: assertion_config(item) for item in rules}
        column["assertions"] = assertions
