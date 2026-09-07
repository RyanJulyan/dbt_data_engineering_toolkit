"""Small reusable validation primitives with no orchestration knowledge."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Hashable, Iterable, TypeVar

from ...errors import DiagnosticCategory
from ...models import ColumnMapping
from ...operational import JsonValue
from ...registry import Operator, OperatorParameter

if TYPE_CHECKING:
    from .context import ValidationContext

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
TYPE_ALIASES = {
    "varchar": "string",
    "char": "string",
    "text": "string",
    "decimal": "number",
    "numeric": "number",
    "double": "number",
    "float": "number",
    "real": "number",
    "int": "integer",
    "smallint": "integer",
    "bigint": "integer",
    "datetime": "timestamp",
}
NUMERIC_SHAPE = re.compile(
    r"^\s*(?:decimal|number|numeric)\s*\(\s*(?P<precision>\d+)\s*,\s*(?P<scale>\d+)\s*\)",
    re.IGNORECASE,
)

HashableValue = TypeVar("HashableValue", bound=Hashable)


def canonical_type(value: str) -> str:
    normal = value.strip().casefold()
    base = re.split(r"[<(]", normal, maxsplit=1)[0].strip()
    return TYPE_ALIASES.get(base, base)


def numeric_shape(value: str | None) -> tuple[int, int] | None:
    """Return declared numeric precision/scale when the physical type includes it."""

    if not value or (match := NUMERIC_SHAPE.match(value)) is None:
        return None
    return int(match.group("precision")), int(match.group("scale"))


def duplicates(values: Iterable[HashableValue]) -> set[HashableValue]:
    return {value for value, count in Counter(values).items() if count > 1}


def mapping_row(mapping: ColumnMapping) -> int | None:
    return mapping.steps[0].workbook_row if mapping.steps else None


def validate_identifier(
    context: "ValidationContext",
    value: str,
    label: str,
    sheet: str,
    row: int | None = None,
    *,
    code: str,
    category: DiagnosticCategory,
) -> None:
    if not IDENTIFIER.fullmatch(value):
        context.add(
            code,
            category,
            sheet,
            row,
            f"{label} {value!r} is not a safe dbt identifier",
            "Use lowercase snake_case beginning with a letter.",
            identifier=value,
        )


def validate_parameter(
    context: "ValidationContext",
    name: str,
    value: JsonValue,
    definition: OperatorParameter,
    sheet: str,
    row: int,
    *,
    code: str,
    category: DiagnosticCategory,
) -> None:
    if definition.parameter_type == "choice" and value not in definition.values:
        context.add(
            code,
            category,
            sheet,
            row,
            f"{name.replace('_', ' ').title()} has unsupported value {value!r}",
            f"Choose one of: {', '.join(map(str, definition.values))}.",
        )
    if definition.parameter_type == "integer" and not isinstance(value, int):
        context.add(code, category, sheet, row, f"{name} must be a whole number")
    if definition.parameter_type in {"integer", "number"} and definition.minimum is not None:
        if not isinstance(value, int | float):
            context.add(code, category, sheet, row, f"{name} must be numeric")
        elif value < definition.minimum:
            context.add(
                code,
                category,
                sheet,
                row,
                f"{name} must be at least {definition.minimum}",
            )


def step_output_type(
    current_type: str, operator: Operator, parameters: dict[str, JsonValue]
) -> str:
    if operator.output_type == "configured":
        current_type = canonical_type(str(parameters.get("data_type", current_type)))
    elif operator.output_type != "same":
        current_type = canonical_type(operator.output_type)
    if "format_pattern" in parameters or "format_case" in parameters:
        return "string"
    return current_type
