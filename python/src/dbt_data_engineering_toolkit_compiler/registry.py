"""Load the controlled BA-safe operator registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files
from pathlib import Path

import yaml

from .operational import JsonValue
from .version import OPERATOR_REGISTRY_VERSION


class OperatorKind(StrEnum):
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"


@dataclass(frozen=True, slots=True)
class OperatorParameter:
    parameter_type: str
    required: bool = False
    values: tuple[JsonValue, ...] = ()
    minimum: int | float | None = None
    default: JsonValue | None = None


@dataclass(frozen=True, slots=True)
class Operator:
    key: str
    label: str
    kind: OperatorKind
    macro: str
    input_types: tuple[str, ...]
    output_type: str
    parameters: dict[str, OperatorParameter]


class OperatorRegistry:
    def __init__(self, operators: list[Operator]):
        self.operators = operators
        self._by_name = {
            name.casefold(): operator
            for operator in operators
            for name in (operator.key, operator.label)
        }

    @classmethod
    def load(cls, path: Path | None = None) -> "OperatorRegistry":
        if path is None:
            path = Path(
                str(files("dbt_data_engineering_toolkit_compiler") / "resources" / "operators.yml")
            )
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        operators = [
            Operator(
                key=item["key"],
                label=item["label"],
                kind=OperatorKind(item["kind"]),
                macro=item["macro"],
                input_types=tuple(item.get("input_types", ["any"])),
                output_type=item.get("output_type", "same"),
                parameters={
                    name: OperatorParameter(
                        parameter_type=str(definition.get("type") or "string"),
                        required=bool(definition.get("required", False)),
                        values=tuple(definition.get("values") or ()),
                        minimum=definition.get("minimum"),
                        default=definition.get("default"),
                    )
                    for name, definition in (item.get("parameters") or {}).items()
                },
            )
            for item in payload["operators"]
            if item.get("ba_safe", False)
        ]
        return cls(operators)

    def resolve(self, name: str) -> Operator | None:
        return self._by_name.get(name.strip().casefold())

    def labels(self, kind: str | OperatorKind) -> list[str]:
        expected = OperatorKind(kind)
        return [item.label for item in self.operators if item.kind == expected]

    def fingerprint(self) -> str:
        """Stable fingerprint embedded in workbooks and generation manifests."""

        payload = {
            "version": OPERATOR_REGISTRY_VERSION,
            "operators": [
                {
                    "key": item.key,
                    "label": item.label,
                    "kind": item.kind.value,
                    "macro": item.macro,
                    "input_types": item.input_types,
                    "output_type": item.output_type,
                    "parameters": {
                        name: {
                            "type": parameter.parameter_type,
                            "required": parameter.required,
                            "values": parameter.values,
                            "minimum": parameter.minimum,
                            "default": parameter.default,
                        }
                        for name, parameter in sorted(item.parameters.items())
                    },
                }
                for item in sorted(self.operators, key=lambda value: value.key)
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
