"""Model graph inputs and target schema declaration validation."""

from __future__ import annotations

import re

from ...errors import DiagnosticCategory
from ...models import Materialization, SchemaImplementation
from .common import duplicates, validate_identifier
from .context import ValidationContext


class ModelAndSchemaValidator:
    def validate(self, context: ValidationContext) -> None:
        spec = context.spec
        for model in spec.models:
            if model.materialization == Materialization.INCREMENTAL:
                context.add(
                    "DET-MOD-003",
                    DiagnosticCategory.MODEL,
                    "DET Models",
                    None,
                    f"{model.name}: incremental materialization is intentionally unavailable in V2.3.0",
                    "Use view, table, or ephemeral until watermark and merge semantics are configured explicitly.",
                )
            if model.enabled and not model.inputs:
                context.add(
                    "DET-MOD-004",
                    DiagnosticCategory.MODEL,
                    "DET Model Inputs",
                    None,
                    f"{model.name} has no input relations",
                )
            if len(model.inputs) != len(set(model.inputs)):
                context.add(
                    "DET-MOD-005",
                    DiagnosticCategory.MODEL,
                    "DET Model Inputs",
                    None,
                    f"{model.name} repeats an input relation",
                )
            for relation in model.inputs:
                if relation not in context.all_relations:
                    context.add(
                        "DET-MOD-006",
                        DiagnosticCategory.MODEL,
                        "DET Model Inputs",
                        None,
                        f"{model.name} references unknown input {relation!r}",
                        "Add it to DET Sources or DET Models, or correct the input row.",
                    )

        for object_name, field in duplicates(context.schema_keys):
            prop = next(
                item
                for item in spec.schema_properties
                if item.object_name == object_name and item.name == field
            )
            context.add(
                "DET-SCH-001",
                DiagnosticCategory.MODEL,
                prop.workbook_sheet or f"Schema {object_name}",
                prop.workbook_row,
                f"duplicate contract field {object_name}.{field}",
            )
        for prop in spec.schema_properties:
            sheet = prop.workbook_sheet or "Schema"
            if prop.object_name not in context.model_names:
                context.add(
                    "DET-SCH-002",
                    DiagnosticCategory.MODEL,
                    sheet,
                    prop.workbook_row,
                    f"schema object {prop.object_name!r} has no DET Model",
                )
            if prop.implementation == SchemaImplementation.MAPPED:
                validate_identifier(
                    context,
                    prop.name,
                    "contract field",
                    sheet,
                    prop.workbook_row,
                    code="DET-SCH-003",
                    category=DiagnosticCategory.MODEL,
                )
            elif not re.fullmatch(r"^_det_[a-z0-9_]+$", prop.name):
                context.add(
                    "DET-SCH-004",
                    DiagnosticCategory.MODEL,
                    sheet,
                    prop.workbook_row,
                    f"operational field {prop.name!r} must use the _det_ prefix",
                )
            if not prop.logical_type:
                context.add(
                    "DET-SCH-005",
                    DiagnosticCategory.MODEL,
                    sheet,
                    prop.workbook_row,
                    "Logical Type is blank",
                )
        for model_name in context.enabled_models:
            if not any(item.object_name == model_name for item in spec.schema_properties):
                context.add(
                    "DET-SCH-006",
                    DiagnosticCategory.MODEL,
                    "Workbook",
                    None,
                    f"enabled model {model_name} has no Schema {model_name} sheet",
                )
