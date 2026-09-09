"""ODCS quality-control and compiler build-configuration validation."""

from __future__ import annotations

import re

from ...adapters import AdapterRegistry
from ...errors import DiagnosticCategory
from ...models import ContractQualityRule
from ...version import COMPILER_VERSION, DEFAULT_TOOLKIT_REVISION
from .context import ValidationContext

QUALITY_METRICS = {
    "rowCount",
    "duplicateValues",
    "nullValues",
    "missingValues",
    "invalidValues",
}
QUALITY_DIMENSIONS = {
    "accuracy",
    "completeness",
    "conformity",
    "consistency",
    "coverage",
    "timeliness",
    "uniqueness",
}
QUALITY_THRESHOLDS = {
    "mustBe",
    "mustNotBe",
    "mustBeGreaterThan",
    "mustBeGreaterOrEqualTo",
    "mustBeLessThan",
    "mustBeLessOrEqualTo",
    "mustBeBetween",
    "mustNotBeBetween",
}


class QualityAndBuildValidator:
    def __init__(self, adapters: AdapterRegistry | None = None) -> None:
        self.adapters = adapters or AdapterRegistry.default()

    def validate(self, context: ValidationContext) -> None:
        quality_ids: set[str] = set()
        property_keys = set(context.schema_keys)
        for rule in context.spec.quality:
            source = rule.workbook_sheet
            if rule.object_name not in context.model_names:
                context.add(
                    "DET-QLT-001",
                    DiagnosticCategory.QUALITY,
                    source,
                    rule.workbook_row,
                    f"unknown Object {rule.object_name!r}",
                )
            if (
                rule.property_name
                and (
                    rule.object_name,
                    rule.property_name,
                )
                not in property_keys
            ):
                context.add(
                    "DET-QLT-002",
                    DiagnosticCategory.QUALITY,
                    source,
                    rule.workbook_row,
                    f"unknown property {rule.object_name}.{rule.property_name}",
                )
            if rule.rule_id in quality_ids:
                context.add(
                    "DET-QLT-003",
                    DiagnosticCategory.QUALITY,
                    source,
                    rule.workbook_row,
                    f"duplicate Rule ID {rule.rule_id!r}",
                )
            quality_ids.add(rule.rule_id)
            if rule.rule_type == "library":
                self._validate_library_rule(context, rule)
            elif rule.rule_type == "sql":
                self._validate_sql_rule(context, rule)
            elif rule.rule_type == "custom":
                self._validate_custom_rule(context, rule)
            elif rule.rule_type == "text":
                if not rule.description:
                    context.add(
                        "DET-QLT-012",
                        DiagnosticCategory.QUALITY,
                        source,
                        rule.workbook_row,
                        "text quality rule requires Description",
                    )
            else:
                context.add(
                    "DET-QLT-005",
                    DiagnosticCategory.QUALITY,
                    source,
                    rule.workbook_row,
                    f"unsupported Quality Type {rule.rule_type!r}",
                    "Choose library, sql, custom, or text.",
                )

            if rule.dimension and rule.dimension not in QUALITY_DIMENSIONS:
                context.add(
                    "DET-QLT-007",
                    DiagnosticCategory.QUALITY,
                    source,
                    rule.workbook_row,
                    f"unsupported Dimension {rule.dimension!r}",
                )
        self._validate_build(context)

    @staticmethod
    def _validate_library_rule(context: ValidationContext, rule: ContractQualityRule) -> None:
        if rule.metric not in QUALITY_METRICS:
            context.add(
                "DET-QLT-004",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                f"unsupported library Metric {rule.metric!r}",
                "Choose one of: " + ", ".join(sorted(QUALITY_METRICS)) + ".",
            )
        QualityAndBuildValidator._validate_threshold(context, rule)

    @staticmethod
    def _validate_sql_rule(context: ValidationContext, rule: ContractQualityRule) -> None:
        if not rule.query:
            context.add(
                "DET-QLT-008",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                "SQL quality rule requires Query (SQL)",
            )
        QualityAndBuildValidator._validate_threshold(context, rule)

    @staticmethod
    def _validate_custom_rule(context: ValidationContext, rule: ContractQualityRule) -> None:
        if not rule.engine:
            context.add(
                "DET-QLT-009",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                "custom quality rule requires Quality Engine (Custom)",
            )
        if rule.implementation is None:
            context.add(
                "DET-QLT-010",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                "custom quality rule requires Implementation (Custom)",
            )
        if rule.threshold:
            context.add(
                "DET-QLT-011",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                "custom quality rules cannot use a library Threshold Operator",
                "Put vendor-specific settings in Implementation (Custom) or ODCS Passthrough (JSON).",
            )

    @staticmethod
    def _validate_threshold(context: ValidationContext, rule: ContractQualityRule) -> None:
        if rule.threshold not in QUALITY_THRESHOLDS:
            context.add(
                "DET-QLT-006",
                DiagnosticCategory.QUALITY,
                rule.workbook_sheet,
                rule.workbook_row,
                f"unsupported Threshold {rule.threshold!r}",
                "Choose a supported ODCS threshold operator and enter its value.",
            )

    def _validate_build(self, context: ValidationContext) -> None:
        build = context.spec.build
        if build.contract_test_authority != "datacontract":
            context.add(
                "DET-BLD-001",
                DiagnosticCategory.BUILD,
                "DET Build",
                None,
                f"Contract Test Authority must be 'datacontract' in V{COMPILER_VERSION}",
                "ODCS and Data Contract CLI own schema-derived tests; DET owns transformations and runtime routing.",
            )
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", build.toolkit_git_env):
            context.add(
                "DET-BLD-002",
                DiagnosticCategory.BUILD,
                "DET Build",
                None,
                "Toolkit Git Env must be an uppercase environment-variable name",
                "Use DBT_DATA_ENGINEERING_TOOLKIT_GIT_URL or another NAME_WITH_UNDERSCORES.",
            )
        if not build.toolkit_revision:
            context.add(
                "DET-BLD-003",
                DiagnosticCategory.BUILD,
                "DET Build",
                None,
                "Toolkit Revision is blank",
                f"Pin a published tag or immutable commit, for example {DEFAULT_TOOLKIT_REVISION}.",
            )
        provider = self.adapters.get(build.adapter)
        if provider is None:
            context.add(
                "DET-BLD-004",
                DiagnosticCategory.BUILD,
                "DET Build",
                None,
                f"unsupported Adapter {build.adapter!r}",
                "Choose one of: " + ", ".join(self.adapters.names()) + ".",
            )
            return
        for model in context.spec.models:
            materialization = model.materialization.value
            if materialization == "incremental" and not provider.supports_incremental:
                continue  # DET-MOD-001 owns the clearer unsupported-incremental message.
            if materialization not in provider.supported_materializations:
                context.add(
                    "DET-BLD-005",
                    DiagnosticCategory.BUILD,
                    "DET Models",
                    None,
                    f"{model.name}: {materialization!r} is not supported by adapter "
                    f"{provider.name!r}",
                )
            if model.enforce_contract and not provider.supports_enforced_contracts:
                context.add(
                    "DET-BLD-006",
                    DiagnosticCategory.BUILD,
                    "DET Models",
                    None,
                    f"{model.name}: enforced contracts are not supported by adapter "
                    f"{provider.name!r}",
                )
