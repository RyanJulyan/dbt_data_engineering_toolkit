"""Interpret DET source, source-column, model-input, and model sheets."""

from __future__ import annotations

from collections import defaultdict

from ...models import (
    Materialization,
    ModelLayer,
    ModelSpecification,
    SourceColumn,
    SourceSpecification,
)
from .common import (
    WorkbookParseContext,
    boolean,
    integer,
    optional_text,
    rows,
    slug,
    string_list,
)


class SourcesAndModelsInterpreter:
    def interpret(
        self, context: WorkbookParseContext
    ) -> tuple[list[SourceSpecification], list[SourceColumn], list[ModelSpecification]]:
        sources = self._sources(context)
        columns = self._columns(context)
        models = self._models(context)
        return sources, columns, models

    @staticmethod
    def _sources(context: WorkbookParseContext) -> list[SourceSpecification]:
        result: list[SourceSpecification] = []
        for row_number, row in rows(context.workbook.sheet("DET Sources")):
            try:
                result.append(
                    SourceSpecification(
                        relation=slug(row.get("Relation")),
                        source_name=slug(row.get("Source Name")),
                        table_name=slug(row.get("Table Name")),
                        database=optional_text(row.get("Database")),
                        schema_name=optional_text(row.get("Schema")),
                        description=optional_text(row.get("Description")),
                    )
                )
            except Exception as exc:
                context.add("DET Sources", row_number, str(exc), code="DET-WBK-020")
        return result

    @staticmethod
    def _columns(context: WorkbookParseContext) -> list[SourceColumn]:
        result: list[SourceColumn] = []
        for row_number, row in rows(context.workbook.sheet("DET Source Schema")):
            try:
                result.append(
                    SourceColumn(
                        relation=slug(row.get("Relation")),
                        name=slug(row.get("Field")),
                        logical_type=slug(row.get("Logical Type")),
                        physical_type=optional_text(row.get("Physical Type")),
                        nullable=boolean(row.get("Nullable"), True),
                        unique=boolean(row.get("Unique")),
                        description=optional_text(row.get("Description")),
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add("DET Source Schema", row_number, str(exc), code="DET-WBK-021")
        return result

    @staticmethod
    def _models(context: WorkbookParseContext) -> list[ModelSpecification]:
        input_rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for row_number, row in rows(context.workbook.sheet("DET Model Inputs")):
            try:
                input_rows[slug(row.get("Model"))].append(
                    (integer(row.get("Order"), 1), slug(row.get("Input Relation")))
                )
            except Exception as exc:
                context.add("DET Model Inputs", row_number, str(exc), code="DET-WBK-022")
        result: list[ModelSpecification] = []
        for row_number, row in rows(context.workbook.sheet("DET Models")):
            model_name = slug(row.get("Model"))
            try:
                result.append(
                    ModelSpecification(
                        name=model_name,
                        layer=ModelLayer(slug(row.get("Layer")).casefold()),
                        materialization=Materialization(
                            (slug(row.get("Materialization")) or "view").casefold()
                        ),
                        description=optional_text(row.get("Description")),
                        grain=string_list(row.get("Grain")),
                        inputs=[relation for _, relation in sorted(input_rows.get(model_name, []))],
                        audit_source=optional_text(row.get("Audit Source")),
                        incremental_strategy=optional_text(row.get("Incremental Strategy")),
                        enforce_contract=boolean(row.get("Enforce Contract")),
                        enabled=boolean(row.get("Enabled"), True),
                    )
                )
            except Exception as exc:
                context.add("DET Models", row_number, str(exc), code="DET-WBK-023")
        return result
