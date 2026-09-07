"""Interpret DET transformation, rule, lookup, and relationship sheets."""

from __future__ import annotations

from collections import defaultdict

from ...models import (
    Cardinality,
    ColumnMapping,
    FailureMode,
    JoinType,
    LookupEntry,
    Relationship,
    SourceColumn,
    TransformationStep,
    ValidationRule,
)
from ...operational import JsonValue
from .common import (
    OPERATIONAL_PARAMETERS_SHEET,
    OPERATIONAL_RULES_SHEET,
    WorkbookParseContext,
    integer,
    json_value,
    optional_text,
    parameter,
    rows,
    slug,
)


class MappingsAndRulesInterpreter:
    def interpret(
        self,
        context: WorkbookParseContext,
        source_columns: list[SourceColumn],
    ) -> tuple[
        list[ColumnMapping],
        list[ValidationRule],
        list[LookupEntry],
        list[Relationship],
    ]:
        return (
            self._mappings(context, source_columns),
            self._rules(context),
            self._lookups(context),
            self._relationships(context),
        )

    @staticmethod
    def _mappings(
        context: WorkbookParseContext, source_columns: list[SourceColumn]
    ) -> list[ColumnMapping]:
        parameters: dict[tuple[str, str, int], dict[str, JsonValue]] = defaultdict(dict)
        for row_number, row in rows(context.workbook.sheet("DET Parameters")):
            try:
                name, value = parameter(row.get("Parameter"), row.get("Value"))
                key = (
                    slug(row.get("Model")),
                    slug(row.get("Target Field")),
                    integer(row.get("Step"), 1),
                )
                parameters[key][name] = value
            except Exception as exc:
                context.add("DET Parameters", row_number, str(exc), code="DET-WBK-030")
        grouped: dict[tuple[str, str, str, str], list[TransformationStep]] = defaultdict(list)
        source_types = {(item.relation, item.name): item.logical_type for item in source_columns}
        for row_number, row in rows(context.workbook.sheet("DET Mapping")):
            model = slug(row.get("Model"))
            target = slug(row.get("Target Field"))
            relation = slug(row.get("Source Relation"))
            field = slug(row.get("Source Field"))
            step_number = integer(row.get("Step"), 1)
            try:
                grouped[(model, target, relation, field)].append(
                    TransformationStep(
                        step=step_number,
                        operation=slug(row.get("Operation")),
                        parameters=parameters.get((model, target, step_number), {}),
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add("DET Mapping", row_number, str(exc), code="DET-WBK-031")
        return [
            ColumnMapping(
                model=model,
                target_field=target,
                source_relation=relation,
                source_field=field,
                source_type=source_types.get((relation, field), "unknown"),
                steps=steps,
            )
            for (model, target, relation, field), steps in grouped.items()
        ]

    @staticmethod
    def _rules(context: WorkbookParseContext) -> list[ValidationRule]:
        parameters: dict[tuple[str, str], dict[str, JsonValue]] = defaultdict(dict)
        for row_number, row in rows(context.workbook.sheet(OPERATIONAL_PARAMETERS_SHEET)):
            try:
                name, value = parameter(row.get("Parameter"), row.get("Value"))
                key = (slug(row.get("Model")), slug(row.get("Rule Name")))
                parameters[key][name] = value
            except Exception as exc:
                context.add(
                    OPERATIONAL_PARAMETERS_SHEET,
                    row_number,
                    str(exc),
                    code="DET-WBK-032",
                )
        result: list[ValidationRule] = []
        for row_number, row in rows(context.workbook.sheet(OPERATIONAL_RULES_SHEET)):
            model = slug(row.get("Model"))
            name = slug(row.get("Rule Name"))
            operation = slug(row.get("Operation"))
            values = dict(parameters.get((model, name), {}))
            if operation.casefold() in {"no_future_date", "not in future"}:
                values = {
                    "operator": "<=",
                    "compare_to": "current_date",
                    **values,
                }
            try:
                result.append(
                    ValidationRule(
                        model=model,
                        name=name,
                        target_field=slug(row.get("Target Field")),
                        operation=operation,
                        parameters=values,
                        failure=FailureMode(slug(row.get("Failure")).casefold()),
                        description=optional_text(row.get("Description")),
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add(OPERATIONAL_RULES_SHEET, row_number, str(exc), code="DET-WBK-033")
        return result

    @staticmethod
    def _lookups(context: WorkbookParseContext) -> list[LookupEntry]:
        result: list[LookupEntry] = []
        for row_number, row in rows(context.workbook.sheet("DET Lookups")):
            try:
                result.append(
                    LookupEntry(
                        lookup=slug(row.get("Lookup")),
                        source_value=slug(row.get("Source Value")),
                        target_value=json_value(row.get("Target Value")),
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add("DET Lookups", row_number, str(exc), code="DET-WBK-034")
        return result

    @staticmethod
    def _relationships(context: WorkbookParseContext) -> list[Relationship]:
        result: list[Relationship] = []
        for row_number, row in rows(context.workbook.sheet("DET Relationships")):
            try:
                result.append(
                    Relationship(
                        model=slug(row.get("Model")),
                        left_relation=slug(row.get("Left Relation")),
                        right_relation=slug(row.get("Right Relation")),
                        join_type=JoinType(slug(row.get("Join Type")).casefold()),
                        left_key=slug(row.get("Left Key")),
                        right_key=slug(row.get("Right Key")),
                        cardinality=Cardinality(slug(row.get("Cardinality")).casefold()),
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add("DET Relationships", row_number, str(exc), code="DET-WBK-035")
        return result
