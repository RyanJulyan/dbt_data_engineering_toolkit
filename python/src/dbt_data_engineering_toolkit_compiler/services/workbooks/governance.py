"""Interpret official governance sheets and DET build controls."""

from __future__ import annotations

import hashlib
import json

from ...brokers.workbooks import CellValue
from ...models import (
    BuildConfiguration,
    ContractQualityRule,
    ProductMetadata,
    Role,
    Server,
    SlaProperty,
    SupportChannel,
    TeamMember,
)
from ...operational import JsonValue
from ...version import DEFAULT_TOOLKIT_REVISION
from .common import (
    WorkbookParseContext,
    boolean,
    json_value,
    key_values,
    normal_key,
    optional,
    optional_text,
    remove_blank_mapping,
    rows,
    slug,
)


def _quality_json_value(value: CellValue) -> JsonValue:
    converted = json_value(value)
    if not isinstance(converted, str):
        return converted
    try:
        return json.loads(converted)
    except json.JSONDecodeError:
        return converted


def _quality_passthrough(
    context: WorkbookParseContext,
    row_number: int,
    value: CellValue,
) -> dict[str, JsonValue]:
    if optional(value) is None:
        return {}
    try:
        payload = json.loads(str(value))
    except json.JSONDecodeError as exc:
        context.add(
            "Quality",
            row_number,
            f"ODCS Passthrough (JSON) is invalid: {exc}",
            code="DET-WBK-047",
            hint="Enter a JSON object containing additional ODCS DataQuality fields.",
        )
        return {}
    if not isinstance(payload, dict):
        context.add(
            "Quality",
            row_number,
            "ODCS Passthrough (JSON) must be a JSON object",
            code="DET-WBK-047",
            hint='Use an object such as {"unit":"percent","method":"reconciliation"}.',
        )
        return {}
    return payload


def _quality_rule_id(
    *,
    object_name: str,
    property_name: str | None,
    rule_type: str,
    metric: str | None,
    query: str | None,
    engine: str | None,
) -> str:
    primary = metric or engine or rule_type
    base = normal_key("_".join(filter(None, (object_name, property_name, primary))))
    if rule_type in {"library", "text"}:
        return base
    signature = json.dumps(
        {"type": rule_type, "query": query, "engine": engine},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{base}_{hashlib.sha256(signature.encode()).hexdigest()[:10]}"


class GovernanceInterpreter:
    def interpret(
        self, context: WorkbookParseContext, product: ProductMetadata
    ) -> tuple[
        list[Server],
        list[TeamMember],
        list[SlaProperty],
        list[ContractQualityRule],
        list[Role],
        list[SupportChannel],
        BuildConfiguration,
    ]:
        servers = self._servers(context)
        team = self._team(context)
        if team and product.owner_email is None:
            product.owner_email = team[0].email
        return (
            servers,
            team,
            self._sla(context),
            self._quality(context),
            self._roles(context),
            self._support(context),
            self._build(context),
        )

    @staticmethod
    def _servers(context: WorkbookParseContext) -> list[Server]:
        sheet = context.workbook.sheet("Servers")
        type_rows = {
            "bigquery": {"database": 18},
            "databricks": {"host": 23, "schema_name": 22},
            "glue": {"account": 26, "database": 27},
            "postgres": {
                "host": 36,
                "port": 37,
                "database": 38,
                "schema_name": 39,
            },
            "snowflake": {
                "host": 48,
                "port": 49,
                "account": 50,
                "database": 51,
                "schema_name": 53,
            },
            "sqlserver": {
                "host": 56,
                "port": 57,
                "database": 58,
                "schema_name": 59,
            },
            "oracle": {"host": 62, "port": 63},
            "custom": {
                "account": 67,
                "database": 69,
                "host": 74,
                "port": 77,
                "schema_name": 81,
            },
        }
        result: list[Server] = []
        for column in range(3, sheet.max_column + 1):
            name = slug(sheet.cell(4, column))
            if not name:
                continue
            server_type = slug(sheet.cell(8, column))
            locations = type_rows.get(server_type, type_rows["custom"])
            values = {key: sheet.cell(row, column) for key, row in locations.items()}
            try:
                result.append(
                    Server(
                        name=name,
                        server_type=server_type,
                        environment=slug(sheet.cell(5, column)),
                        account=optional_text(values.get("account")),
                        database=optional_text(values.get("database")),
                        schema_name=optional_text(values.get("schema_name")),
                        host=optional_text(values.get("host")),
                        port=(
                            int(str(values["port"]))
                            if optional(values.get("port")) is not None
                            else None
                        ),
                    )
                )
            except Exception as exc:
                context.add("Servers", 4, str(exc), code="DET-WBK-040")
        return result

    @staticmethod
    def _team(context: WorkbookParseContext) -> list[TeamMember]:
        result: list[TeamMember] = []
        for row_number, row in rows(context.workbook.sheet("Team"), header_row=4, data_row=5):
            if not optional(row.get("Username")):
                continue
            try:
                username = slug(row.get("Username"))
                result.append(
                    TeamMember(
                        username=username,
                        name=optional_text(row.get("Name")),
                        role=optional_text(row.get("Role")),
                        email=username if "@" in username else None,
                    )
                )
            except Exception as exc:
                context.add("Team", row_number, str(exc), code="DET-WBK-041")
        return result

    @staticmethod
    def _sla(context: WorkbookParseContext) -> list[SlaProperty]:
        result: list[SlaProperty] = []
        for row_number, row in rows(context.workbook.sheet("SLA"), header_row=6, data_row=7):
            if not optional(row.get("Property")):
                continue
            try:
                result.append(
                    SlaProperty(
                        name=slug(row.get("Property")),
                        value=json_value(row.get("Value")),
                        unit=optional_text(row.get("Unit")),
                        description=optional_text(row.get("Driver")),
                    )
                )
            except Exception as exc:
                context.add("SLA", row_number, str(exc), code="DET-WBK-042")
        return result

    @classmethod
    def _quality(cls, context: WorkbookParseContext) -> list[ContractQualityRule]:
        return cls._official_quality(context)

    @staticmethod
    def _official_quality(context: WorkbookParseContext) -> list[ContractQualityRule]:
        result: list[ContractQualityRule] = []
        for row_number, row in rows(context.workbook.sheet("Quality"), header_row=4, data_row=5):
            object_name = slug(row.get("Schema"))
            quality_values = [
                row.get("Quality Type"),
                row.get("Description"),
                row.get("Rule (Library)"),
                row.get("Query (SQL)"),
                row.get("Quality Engine (Custom)"),
                row.get("Implementation (Custom)"),
                row.get("Threshold Operator"),
                row.get("Threshold Value"),
                row.get("Severity"),
                row.get("Scheduler"),
                row.get("Schedule"),
                row.get("Rule ID"),
                row.get("Dimension"),
                row.get("ODCS Passthrough (JSON)"),
            ]
            if not object_name:
                if any(optional(value) is not None for value in quality_values):
                    context.add(
                        "Quality",
                        row_number,
                        "a quality rule has values but no Schema",
                        code="DET-WBK-045",
                        hint="Choose the contract schema that owns this quality rule.",
                    )
                continue
            metric = optional_text(row.get("Rule (Library)"))
            query = optional_text(row.get("Query (SQL)"))
            engine = optional_text(row.get("Quality Engine (Custom)"))
            implementation = _quality_json_value(row.get("Implementation (Custom)"))
            rule_type = slug(row.get("Quality Type")).casefold()
            if not rule_type:
                rule_type = (
                    "sql"
                    if query
                    else "custom"
                    if engine or implementation is not None
                    else "library"
                    if metric
                    else "text"
                )
            threshold = optional_text(row.get("Threshold Operator"))
            value = _quality_json_value(row.get("Threshold Value"))
            passthrough = _quality_passthrough(
                context,
                row_number,
                row.get("ODCS Passthrough (JSON)"),
            )
            rule_id = slug(row.get("Rule ID")) or _quality_rule_id(
                object_name=object_name,
                property_name=optional_text(row.get("Property")),
                rule_type=rule_type,
                metric=metric,
                query=query,
                engine=engine,
            )
            try:
                result.append(
                    ContractQualityRule(
                        object_name=object_name,
                        property_name=optional_text(row.get("Property")),
                        rule_id=rule_id,
                        rule_type=rule_type,
                        metric=metric,
                        threshold=threshold,
                        value=value,
                        dimension=optional_text(row.get("Dimension")),
                        description=optional_text(row.get("Description")),
                        query=query,
                        engine=engine,
                        implementation=implementation,
                        severity=optional_text(row.get("Severity")),
                        scheduler=optional_text(row.get("Scheduler")),
                        schedule=optional_text(row.get("Schedule")),
                        odcs_fields=passthrough,
                        workbook_sheet="Quality",
                        workbook_row=row_number,
                    )
                )
            except Exception as exc:
                context.add("Quality", row_number, str(exc), code="DET-WBK-046")
        return result

    @staticmethod
    def _roles(context: WorkbookParseContext) -> list[Role]:
        return [
            Role.model_validate(
                remove_blank_mapping(
                    {
                        "role": row.get("Role"),
                        "description": row.get("Description"),
                        "access": row.get("Access"),
                    }
                )
            )
            for _, row in rows(context.workbook.sheet("Roles"), header_row=4, data_row=5)
            if optional(row.get("Role"))
        ]

    @staticmethod
    def _support(context: WorkbookParseContext) -> list[SupportChannel]:
        return [
            SupportChannel.model_validate(
                remove_blank_mapping(
                    {
                        "channel": row.get("Channel"),
                        "url": row.get("Channel URL"),
                        "description": row.get("Description"),
                    }
                )
            )
            for _, row in rows(context.workbook.sheet("Support"), header_row=4, data_row=5)
            if optional(row.get("Channel"))
        ]

    @staticmethod
    def _build(context: WorkbookParseContext) -> BuildConfiguration:
        values = key_values(context.workbook.sheet("DET Build"))
        try:
            return BuildConfiguration(
                adapter=slug(values.get("adapter")) or "duckdb",
                profile=slug(values.get("profile")) or "generated_data_product",
                target_schema=slug(values.get("target_schema")) or "main",
                toolkit_git_env=slug(values.get("toolkit_git_env"))
                or "DBT_DATA_ENGINEERING_TOOLKIT_GIT_URL",
                toolkit_revision=slug(values.get("toolkit_revision")) or DEFAULT_TOOLKIT_REVISION,
                allow_many_to_many=boolean(values.get("allow_many_to_many")),
                contract_test_authority=slug(values.get("contract_test_authority"))
                or "datacontract",
            )
        except Exception as exc:
            context.add("DET Build", None, str(exc), code="DET-WBK-044")
            return BuildConfiguration()
