"""Explicit adapter capabilities used by validation and project emission."""

from __future__ import annotations

from dataclasses import dataclass

from .operational import JsonValue


def _env(name: str, default: str | None = None, *, integer: bool = False) -> str:
    default_argument = f", '{default}'" if default is not None else ""
    cast = " | int" if integer else ""
    return "{{ env_var('" + name + "'" + default_argument + ")" + cast + " }}"


@dataclass(frozen=True, slots=True)
class AdapterProvider:
    name: str
    display_name: str
    dbt_dependency: str
    sqlfluff_dialect: str
    logical_types: dict[str, str]
    operational_types: dict[str, str]
    supported_materializations: frozenset[str]
    supports_incremental: bool
    supports_enforced_contracts: bool
    profile_output: dict[str, JsonValue]

    def data_type(self, logical_type: str, physical_type: str | None) -> str:
        return physical_type or self.logical_types.get(
            logical_type.casefold(), logical_type.casefold()
        )

    def operational_type(self, field_name: str) -> str:
        return self.operational_types.get(field_name, self.data_type("string", None))


class AdapterRegistry:
    """Single extension point for warehouse-specific compiler behavior."""

    def __init__(self, providers: list[AdapterProvider]):
        self._providers = {item.name: item for item in providers}

    @classmethod
    def default(cls) -> "AdapterRegistry":
        common_materializations = frozenset({"view", "table", "ephemeral"})
        portable = {
            "string": "varchar",
            "number": "numeric",
            "numeric": "numeric",
            "integer": "bigint",
            "boolean": "boolean",
            "date": "date",
            "timestamp": "timestamp",
            "time": "time",
        }
        return cls(
            [
                AdapterProvider(
                    name="athena",
                    display_name="Amazon Athena",
                    dbt_dependency="dbt-athena-community>=1.10,<2",
                    sqlfluff_dialect="athena",
                    logical_types={
                        **portable,
                        "string": "varchar",
                        "number": "double",
                        "numeric": "decimal(38,6)",
                        "timestamp": "timestamp",
                    },
                    operational_types={
                        "_det_rejections": "array(varchar)",
                        "_det_warnings": "array(varchar)",
                        "_det_loaded_at": "timestamp",
                        "_det_invocation_id": "varchar",
                        "_det_source_system": "varchar",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=False,
                    profile_output={
                        "type": "athena",
                        "database": _env("DET_ATHENA_DATABASE", "awsdatacatalog"),
                        "schema": "__TARGET_SCHEMA__",
                        "s3_staging_dir": _env("DET_ATHENA_S3_STAGING_DIR"),
                        "region_name": _env("DET_ATHENA_REGION", "us-east-1"),
                        "work_group": _env("DET_ATHENA_WORK_GROUP", "primary"),
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="bigquery",
                    display_name="Google BigQuery",
                    dbt_dependency="dbt-bigquery>=1.10,<2",
                    sqlfluff_dialect="bigquery",
                    logical_types={
                        **portable,
                        "string": "string",
                        "number": "float64",
                        "numeric": "numeric",
                        "integer": "int64",
                        "boolean": "bool",
                    },
                    operational_types={
                        "_det_rejections": "array<string>",
                        "_det_warnings": "array<string>",
                        "_det_loaded_at": "timestamp",
                        "_det_invocation_id": "string",
                        "_det_source_system": "string",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "bigquery",
                        "method": "oauth",
                        "project": _env("DET_BIGQUERY_PROJECT"),
                        "dataset": "__TARGET_SCHEMA__",
                        "location": _env("DET_BIGQUERY_LOCATION", "US"),
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="clickhouse",
                    display_name="ClickHouse",
                    dbt_dependency="dbt-clickhouse>=1.10,<2",
                    sqlfluff_dialect="clickhouse",
                    logical_types={
                        **portable,
                        "string": "String",
                        "number": "Float64",
                        "numeric": "Decimal(38,6)",
                        "integer": "Int64",
                        "boolean": "Bool",
                        "date": "Date",
                        "timestamp": "DateTime64(6)",
                        "time": "String",
                    },
                    operational_types={
                        "_det_rejections": "Array(String)",
                        "_det_warnings": "Array(String)",
                        "_det_loaded_at": "DateTime64(6)",
                        "_det_invocation_id": "String",
                        "_det_source_system": "String",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=False,
                    profile_output={
                        "type": "clickhouse",
                        "host": _env("DET_CLICKHOUSE_HOST"),
                        "port": _env("DET_CLICKHOUSE_PORT", "8443", integer=True),
                        "user": _env("DET_CLICKHOUSE_USER", "default"),
                        "password": _env("DBT_ENV_SECRET_DET_CLICKHOUSE_PASSWORD", ""),
                        "schema": "__TARGET_SCHEMA__",
                        "secure": True,
                        "verify": True,
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="databricks",
                    display_name="Databricks",
                    dbt_dependency="dbt-databricks>=1.10,<2",
                    sqlfluff_dialect="databricks",
                    logical_types={
                        **portable,
                        "string": "string",
                        "number": "double",
                        "numeric": "decimal(38,6)",
                        "time": "string",
                    },
                    operational_types={
                        "_det_rejections": "array<string>",
                        "_det_warnings": "array<string>",
                        "_det_loaded_at": "timestamp",
                        "_det_invocation_id": "string",
                        "_det_source_system": "string",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "databricks",
                        "host": _env("DET_DATABRICKS_HOST"),
                        "http_path": _env("DET_DATABRICKS_HTTP_PATH"),
                        "token": _env("DBT_ENV_SECRET_DET_DATABRICKS_TOKEN"),
                        "catalog": _env("DET_DATABRICKS_CATALOG", "hive_metastore"),
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="duckdb",
                    display_name="DuckDB",
                    dbt_dependency="dbt-duckdb>=1.10,<2",
                    sqlfluff_dialect="duckdb",
                    logical_types={
                        **portable,
                        "string": "varchar",
                        "number": "double",
                        "numeric": "decimal(38,6)",
                    },
                    operational_types={
                        "_det_rejections": "varchar[]",
                        "_det_warnings": "varchar[]",
                        "_det_loaded_at": "timestamp with time zone",
                        "_det_invocation_id": "varchar",
                        "_det_source_system": "varchar",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "duckdb",
                        "path": "target/data_product.duckdb",
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="postgres",
                    display_name="Postgres",
                    dbt_dependency="dbt-postgres>=1.10,<2",
                    sqlfluff_dialect="postgres",
                    logical_types={**portable, "string": "text"},
                    operational_types={
                        "_det_rejections": "text[]",
                        "_det_warnings": "text[]",
                        "_det_loaded_at": "timestamp with time zone",
                        "_det_invocation_id": "text",
                        "_det_source_system": "text",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "postgres",
                        "host": _env("DET_POSTGRES_HOST"),
                        "port": _env("DET_POSTGRES_PORT", "5432", integer=True),
                        "user": _env("DET_POSTGRES_USER"),
                        "password": _env("DET_POSTGRES_PASSWORD"),
                        "dbname": _env("DET_POSTGRES_DATABASE"),
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="redshift",
                    display_name="Amazon Redshift",
                    dbt_dependency="dbt-redshift>=1.10,<2",
                    sqlfluff_dialect="redshift",
                    logical_types={
                        **portable,
                        "string": "varchar",
                        "number": "double precision",
                        "numeric": "decimal(38,6)",
                    },
                    operational_types={
                        "_det_rejections": "super",
                        "_det_warnings": "super",
                        "_det_loaded_at": "timestamp",
                        "_det_invocation_id": "varchar",
                        "_det_source_system": "varchar",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "redshift",
                        "host": _env("DET_REDSHIFT_HOST"),
                        "port": _env("DET_REDSHIFT_PORT", "5439", integer=True),
                        "user": _env("DET_REDSHIFT_USER"),
                        "password": _env("DBT_ENV_SECRET_DET_REDSHIFT_PASSWORD"),
                        "dbname": _env("DET_REDSHIFT_DATABASE"),
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="snowflake",
                    display_name="Snowflake",
                    dbt_dependency="dbt-snowflake>=1.10,<2",
                    sqlfluff_dialect="snowflake",
                    logical_types={
                        **portable,
                        "string": "varchar",
                        "integer": "number(38,0)",
                        "timestamp": "timestamp_tz",
                    },
                    operational_types={
                        "_det_rejections": "array",
                        "_det_warnings": "array",
                        "_det_loaded_at": "timestamp_tz",
                        "_det_invocation_id": "varchar",
                        "_det_source_system": "varchar",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=True,
                    profile_output={
                        "type": "snowflake",
                        "account": _env("DET_SNOWFLAKE_ACCOUNT"),
                        "user": _env("DET_SNOWFLAKE_USER"),
                        "password": _env("DBT_ENV_SECRET_DET_SNOWFLAKE_PASSWORD"),
                        "role": _env("DET_SNOWFLAKE_ROLE"),
                        "database": _env("DET_SNOWFLAKE_DATABASE"),
                        "warehouse": _env("DET_SNOWFLAKE_WAREHOUSE"),
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
                AdapterProvider(
                    name="spark",
                    display_name="Apache Spark",
                    dbt_dependency="dbt-spark[PyHive]>=1.10,<2",
                    sqlfluff_dialect="sparksql",
                    logical_types={
                        **portable,
                        "string": "string",
                        "number": "double",
                        "numeric": "decimal(38,6)",
                        "time": "string",
                    },
                    operational_types={
                        "_det_rejections": "array<string>",
                        "_det_warnings": "array<string>",
                        "_det_loaded_at": "timestamp",
                        "_det_invocation_id": "string",
                        "_det_source_system": "string",
                    },
                    supported_materializations=common_materializations,
                    supports_incremental=False,
                    supports_enforced_contracts=False,
                    profile_output={
                        "type": "spark",
                        "method": "thrift",
                        "host": _env("DET_SPARK_HOST"),
                        "port": _env("DET_SPARK_PORT", "10001", integer=True),
                        "user": _env("DET_SPARK_USER", "dbt"),
                        "schema": "__TARGET_SCHEMA__",
                        "threads": 4,
                    },
                ),
            ]
        )

    def get(self, name: str) -> AdapterProvider | None:
        return self._providers.get(name.casefold())

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
