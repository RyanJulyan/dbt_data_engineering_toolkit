"""Compose workbook broker output into the typed data-product IR."""

from __future__ import annotations

from pathlib import Path

from ...brokers.workbooks import OpenpyxlWorkbookBroker, WorkbookBroker
from ...errors import Diagnostic, InvalidWorkbookError, SpecificationValidationError
from ...models import DataProductSpecification
from .common import (
    REQUIRED_SHEETS,
    WorkbookParseContext,
    schema_sheet_names,
)
from .governance import GovernanceInterpreter
from .mappings_rules import MappingsAndRulesInterpreter
from .product_schema import ProductSchemaInterpreter
from .sources_models import SourcesAndModelsInterpreter


class WorkbookInterpretationService:
    """Read through a broker, then delegate each workbook concern."""

    def __init__(
        self,
        workbook_broker: WorkbookBroker | None = None,
        product_schema: ProductSchemaInterpreter | None = None,
        sources_models: SourcesAndModelsInterpreter | None = None,
        mappings_rules: MappingsAndRulesInterpreter | None = None,
        governance: GovernanceInterpreter | None = None,
    ) -> None:
        self.workbook_broker = workbook_broker or OpenpyxlWorkbookBroker()
        self.product_schema = product_schema or ProductSchemaInterpreter()
        self.sources_models = sources_models or SourcesAndModelsInterpreter()
        self.mappings_rules = mappings_rules or MappingsAndRulesInterpreter()
        self.governance = governance or GovernanceInterpreter()

    def load(self, path: Path) -> DataProductSpecification:
        try:
            workbook = self.workbook_broker.read(path)
        except InvalidWorkbookError as exc:
            raise SpecificationValidationError(
                [Diagnostic("Workbook", None, str(exc), code="DET-WBK-001")]
            ) from exc
        missing = sorted(name for name in REQUIRED_SHEETS if name not in workbook.sheetnames)
        if missing:
            raise SpecificationValidationError(
                [
                    Diagnostic(
                        "Workbook",
                        None,
                        f"missing required sheet {name!r}",
                        "Start from the v2.3.0 ODCS-superset template; do not rename its tabs.",
                        code="DET-WBK-002",
                    )
                    for name in missing
                ]
            )
        context = WorkbookParseContext(workbook)
        if not schema_sheet_names(workbook):
            context.add(
                "Workbook",
                None,
                "no populated 'Schema <model>' sheet was found",
                code="DET-WBK-004",
                hint="Copy the official Schema <table_name> sheet and name it for the dbt model.",
            )
        product, schema = self.product_schema.interpret(context)
        sources, source_columns, models = self.sources_models.interpret(context)
        mappings, rules, lookups, relationships = self.mappings_rules.interpret(
            context, source_columns
        )
        servers, team, sla, quality, roles, support, build = self.governance.interpret(
            context, product
        )
        if context.diagnostics:
            raise SpecificationValidationError(context.diagnostics)
        return DataProductSpecification(
            metadata=product,
            schema_properties=schema,
            sources=sources,
            source_columns=source_columns,
            models=models,
            mappings=mappings,
            rules=rules,
            lookups=lookups,
            relationships=relationships,
            servers=servers,
            team=team,
            sla=sla,
            quality=quality,
            roles=roles,
            support=support,
            odcs_passthrough=self.product_schema.odcs_passthrough(context),
            build=build,
        )
