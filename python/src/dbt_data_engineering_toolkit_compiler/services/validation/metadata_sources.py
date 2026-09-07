"""Metadata, identifier, lookup, and source-schema validation."""

from __future__ import annotations

from ...errors import DiagnosticCategory
from .common import canonical_type, duplicates, validate_identifier
from .context import ValidationContext


class MetadataAndSourceValidator:
    def validate(self, context: ValidationContext) -> None:
        spec = context.spec
        if not spec.metadata.product_id:
            context.add(
                "DET-META-001",
                DiagnosticCategory.METADATA,
                "Fundamentals",
                None,
                "Data Product is blank",
                "Enter a stable snake_case ID.",
            )
        else:
            validate_identifier(
                context,
                spec.metadata.product_id,
                "Data Product",
                "Fundamentals",
                code="DET-META-002",
                category=DiagnosticCategory.METADATA,
            )
        if not spec.metadata.name:
            context.add(
                "DET-META-003",
                DiagnosticCategory.METADATA,
                "Fundamentals",
                None,
                "Name is blank",
            )

        for label, names, sheet, code, category in (
            (
                "model",
                context.model_names,
                "DET Models",
                "DET-MOD-001",
                DiagnosticCategory.MODEL,
            ),
            (
                "source relation",
                context.source_names,
                "DET Sources",
                "DET-SRC-001",
                DiagnosticCategory.SOURCE,
            ),
            (
                "lookup",
                context.lookup_names,
                "DET Lookups",
                "DET-MAP-001",
                DiagnosticCategory.MAPPING,
            ),
        ):
            for name in names:
                validate_identifier(
                    context,
                    name,
                    label,
                    sheet,
                    code=code,
                    category=category,
                )

        if len(context.model_names) != len(spec.models):
            context.add(
                "DET-MOD-002",
                DiagnosticCategory.MODEL,
                "DET Models",
                None,
                "Model names must be unique",
            )
        if len(context.source_names) != len(spec.sources):
            context.add(
                "DET-SRC-002",
                DiagnosticCategory.SOURCE,
                "DET Sources",
                None,
                "Relation names must be unique",
            )
        for lookup, source_value in duplicates(
            (item.lookup, item.source_value) for item in spec.lookups
        ):
            context.add(
                "DET-MAP-002",
                DiagnosticCategory.MAPPING,
                "DET Lookups",
                None,
                f"lookup {lookup!r} contains duplicate source value {source_value!r}",
            )
        for source in spec.sources:
            validate_identifier(
                context,
                source.source_name,
                "Source Name",
                "DET Sources",
                code="DET-SRC-003",
                category=DiagnosticCategory.SOURCE,
            )
            validate_identifier(
                context,
                source.table_name,
                "Table Name",
                "DET Sources",
                code="DET-SRC-004",
                category=DiagnosticCategory.SOURCE,
            )

        keys = [(item.relation, item.name) for item in spec.source_columns]
        for relation, field in duplicates(keys):
            context.add(
                "DET-SRC-005",
                DiagnosticCategory.SOURCE,
                "DET Source Schema",
                None,
                f"duplicate source field {relation}.{field}",
            )
        for column in spec.source_columns:
            if column.relation not in context.source_names:
                context.add(
                    "DET-SRC-006",
                    DiagnosticCategory.SOURCE,
                    "DET Source Schema",
                    column.workbook_row,
                    f"{column.relation}.{column.name} references an unknown source relation",
                )
            validate_identifier(
                context,
                column.name,
                "source field",
                "DET Source Schema",
                column.workbook_row,
                code="DET-SRC-007",
                category=DiagnosticCategory.SOURCE,
            )
            if not canonical_type(column.logical_type):
                context.add(
                    "DET-SRC-008",
                    DiagnosticCategory.SOURCE,
                    "DET Source Schema",
                    column.workbook_row,
                    "Logical Type is blank",
                )
        for source in spec.sources:
            if not any(item.relation == source.relation for item in spec.source_columns):
                context.add(
                    "DET-SRC-009",
                    DiagnosticCategory.SOURCE,
                    "DET Source Schema",
                    None,
                    f"{source.relation} has no declared source fields",
                    "Import or enter its source schema before mapping fields.",
                )
