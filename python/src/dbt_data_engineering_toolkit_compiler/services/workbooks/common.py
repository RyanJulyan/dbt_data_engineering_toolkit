"""Technology-neutral DET workbook layout and value conversion helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ...brokers.workbooks import CellValue, SheetData, WorkbookDocument
from ...errors import Diagnostic
from ...operational import JsonValue
from ...workbook_layout import (
    OPERATIONAL_PARAMETERS_SHEET,
    OPERATIONAL_RULES_SHEET,
)

OFFICIAL_SHEETS = {
    "Instructions",
    "Fundamentals",
    "Relationships",
    "Quality",
    "Support",
    "Team",
    "Roles",
    "SLA",
    "Servers",
    "Pricing",
    "Custom Properties",
}
DET_SHEETS = {
    "DET Models",
    "DET Model Inputs",
    "DET Sources",
    "DET Source Schema",
    "DET Mapping",
    "DET Parameters",
    "DET Relationships",
    OPERATIONAL_RULES_SHEET,
    OPERATIONAL_PARAMETERS_SHEET,
    "DET Lookups",
    "DET Build",
    "_DET Lists",
    "_DET Metadata",
}
REQUIRED_SHEETS = OFFICIAL_SHEETS | DET_SHEETS


PARAMETER_ALIASES = {
    "fill_value": "value",
    "minimum": "min_value",
    "maximum": "max_value",
}
BOOLEAN_PARAMETERS = {
    "trim",
    "collapse_whitespace",
    "blank_as_null",
    "keep_plus",
    "preserve_unmapped",
    "case_sensitive",
    "inclusive",
    "allow_null",
}
INTEGER_PARAMETERS = {"precision", "scale"}
NUMBER_PARAMETERS = {"min_value", "max_value"}
LIST_PARAMETERS = {"values"}


@dataclass(slots=True)
class WorkbookParseContext:
    workbook: WorkbookDocument
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def add(
        self,
        sheet: str,
        row: int | None,
        message: str,
        *,
        code: str = "DET-WBK-010",
        hint: str | None = None,
    ) -> None:
        self.diagnostics.append(Diagnostic(sheet, row, message, hint, code=code))


def slug(value: CellValue) -> str:
    return str(value or "").strip()


def boolean(value: CellValue, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    if isinstance(value, bool):
        return value
    normal = str(value).strip().casefold()
    if normal in {"yes", "y", "true", "1"}:
        return True
    if normal in {"no", "n", "false", "0"}:
        return False
    raise ValueError(f"expected Yes or No, got {value!r}")


def string_list(value: CellValue) -> list[str]:
    if value is None or str(value).strip() == "":
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def optional(value: CellValue) -> CellValue:
    return None if value is None or str(value).strip() == "" else value


def optional_text(value: CellValue) -> str | None:
    """Return a trimmed string for an optional workbook cell."""

    return None if optional(value) is None else str(value).strip()


def integer(value: CellValue, default: int = 0) -> int:
    """Convert a workbook cell to an integer with one explicit blank default."""

    return default if optional(value) is None else int(str(value))


def json_value(value: CellValue) -> JsonValue:
    """Convert a physical cell value to the serializable IR value domain."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return value.isoformat()


def normal_key(value: str) -> str:
    return value.strip().casefold().replace("\t", " ").replace(" ", "_").replace("/", "_")


def rows(
    sheet: SheetData,
    *,
    header_row: int = 3,
    data_row: int | None = None,
) -> Iterable[tuple[int, dict[str, CellValue]]]:
    headers = [slug(value) for value in sheet.row(header_row)]
    first_data_row = data_row or header_row + 1
    for row_number, cells in enumerate(
        sheet.iter_rows(min_row=first_data_row), start=first_data_row
    ):
        values = list(cells[: len(headers)])
        if not any(optional(value) is not None for value in values):
            continue
        yield row_number, dict(zip(headers, values, strict=True))


def key_values(sheet: SheetData) -> dict[str, CellValue]:
    result: dict[str, CellValue] = {}
    for _, row in rows(sheet):
        key = optional(row.get("Field"))
        if key is not None:
            result[normal_key(str(key))] = row.get("Value")
    return result


def number(value: CellValue) -> JsonValue:
    if isinstance(value, int | float):
        return value
    text = str(value).strip()
    try:
        converted = float(text)
    except ValueError:
        return str(value)
    return int(converted) if converted.is_integer() else converted


def parameter(name: CellValue, value: CellValue) -> tuple[str, JsonValue]:
    key = PARAMETER_ALIASES.get(normal_key(slug(name)), normal_key(slug(name)))
    if key in BOOLEAN_PARAMETERS:
        converted: JsonValue = boolean(value)
    elif key in INTEGER_PARAMETERS:
        converted = int(str(value))
    elif key in NUMBER_PARAMETERS:
        converted = number(value)
    elif key in LIST_PARAMETERS:
        converted = [json_value(item) for item in string_list(value)]
    else:
        converted = json_value(value)
    return key, converted


def contract_product_id(contract_id: str, data_product: CellValue) -> str:
    if optional(data_product) is not None:
        candidate = slug(data_product).split(":")[-1]
        if candidate:
            return candidate
    return contract_id.split(":")[-1] if contract_id else ""


def schema_sheet_names(workbook: WorkbookDocument) -> list[str]:
    return [
        name
        for name in workbook.sheetnames
        if name.startswith("Schema ") and name != "Schema <table_name>"
    ]


def remove_blank_mapping(
    value: dict[str, CellValue],
) -> dict[str, CellValue]:
    return {key: item for key, item in value.items() if optional(item) is not None}
