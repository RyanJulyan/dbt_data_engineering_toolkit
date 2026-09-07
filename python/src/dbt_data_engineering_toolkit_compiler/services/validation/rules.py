"""Row-level and contract-native rule validation."""

from __future__ import annotations

from ...errors import DiagnosticCategory
from ...models import FailureMode
from ...registry import OperatorKind
from ...workbook_layout import OPERATIONAL_PARAMETERS_SHEET, OPERATIONAL_RULES_SHEET
from .common import canonical_type, validate_parameter
from .context import ValidationContext


class RuleValidator:
    def validate(self, context: ValidationContext) -> None:
        rule_names: set[tuple[str, str]] = set()
        for rule in context.spec.rules:
            operator = context.registry.resolve(rule.operation)
            if operator is None or operator.kind != OperatorKind.VALIDATION:
                context.add(
                    "DET-RUL-001",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f"unknown validation {rule.operation!r}",
                    "Choose an option from the Operation dropdown.",
                )
                continue
            if (rule.model, rule.name) in rule_names:
                context.add(
                    "DET-RUL-002",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f"duplicate rule name {rule.name!r}",
                )
            rule_names.add((rule.model, rule.name))
            target_type = context.inferred_types.get((rule.model, rule.target_field))
            if target_type is None:
                context.add(
                    "DET-RUL-003",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f"{rule.model}.{rule.target_field} is not produced by DET Mapping",
                )
            elif "any" not in operator.input_types and target_type not in {
                canonical_type(item) for item in operator.input_types
            }:
                context.add(
                    "DET-RUL-004",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f'"{operator.label}" requires {", ".join(operator.input_types)}, but {rule.model}.{rule.target_field} is {target_type}',
                )
            for name, definition in operator.parameters.items():
                if definition.required and name not in rule.parameters:
                    context.add(
                        "DET-RUL-005",
                        DiagnosticCategory.RULE,
                        OPERATIONAL_PARAMETERS_SHEET,
                        rule.workbook_row,
                        f'"{operator.label}" requires {name.replace("_", " ")}',
                    )
            for name, value in rule.parameters.items():
                definition = operator.parameters.get(name)
                if definition is None:
                    context.add(
                        "DET-RUL-006",
                        DiagnosticCategory.RULE,
                        OPERATIONAL_PARAMETERS_SHEET,
                        rule.workbook_row,
                        f'"{operator.label}" does not accept parameter {name!r}',
                    )
                else:
                    validate_parameter(
                        context,
                        name,
                        value,
                        definition,
                        OPERATIONAL_PARAMETERS_SHEET,
                        rule.workbook_row,
                        code="DET-RUL-007",
                        category=DiagnosticCategory.RULE,
                    )
            if operator.key == "unique" and rule.failure != FailureMode.FAIL:
                context.add(
                    "DET-RUL-008",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    "Unique only supports Fail build because uniqueness is an aggregate contract",
                    "Remove this operational row and declare Unique on the Schema sheet.",
                )
            prop = context.schema.get((rule.model, rule.target_field))
            if (
                operator.key == "required"
                and rule.failure == FailureMode.FAIL
                and prop
                and not prop.required
            ):
                context.add(
                    "DET-RUL-009",
                    DiagnosticCategory.RULE,
                    prop.workbook_sheet or f"Schema {rule.model}",
                    prop.workbook_row,
                    f"{rule.model}.{rule.target_field}: Required + Fail build must be declared Required in ODCS",
                )
            elif operator.key == "required" and rule.failure == FailureMode.FAIL and prop:
                context.add(
                    "DET-RUL-011",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f"{rule.model}.{rule.target_field}: Required is already owned by the ODCS schema",
                    "Remove this operational row; keep Required selected on the Schema sheet.",
                )
            if operator.key == "unique" and prop and not (prop.unique or prop.primary_key):
                context.add(
                    "DET-RUL-010",
                    DiagnosticCategory.RULE,
                    prop.workbook_sheet or f"Schema {rule.model}",
                    prop.workbook_row,
                    f"{rule.model}.{rule.target_field}: Unique + Fail build must be declared Unique or Primary Key in ODCS",
                )
            elif operator.key == "unique" and prop:
                context.add(
                    "DET-RUL-012",
                    DiagnosticCategory.RULE,
                    OPERATIONAL_RULES_SHEET,
                    rule.workbook_row,
                    f"{rule.model}.{rule.target_field}: Unique is already owned by the ODCS schema",
                    "Remove this operational row; keep Unique or Primary Key on the Schema sheet.",
                )
