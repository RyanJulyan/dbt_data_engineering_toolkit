# Data Engineering Toolkit compiler

The `det` CLI turns the controlled V3.2.0 official-ODCS Excel superset into
canonical ODCS, DET execution metadata, and a readable dbt project. It includes
safe questionnaire-based workbook creation, ODCS/DDL/dbt-to-Excel import and
merge-safe synchronization, source-schema import, cross-sheet semantic/type
validation, atomic post-sync generation, Data Contract synchronization, SQLFluff,
and the isolated `det prove` acceptance flow. Data Contract CLI, dbt Core,
DuckDB, and SQLFluff are default dependencies.

V3.2.0 makes the visible official `Quality` sheet authoritative, preserves
advanced per-rule ODCS values, supports eight production warehouse providers, and adds mandatory
85.01% Python statement coverage. The generated dbt package has 98.53% DuckDB-scoped macro
implementation coverage plus 100% public-API direct execution coverage and supports dbt Core plus
Fusion-compatible projects. External resources
are isolated behind brokers; reusable services interpret workbooks and input
formats; independent components validate with stable diagnostic codes; and one
emitter owns each artifact family. The CLI remains a thin exposer over
`ToolkitApplication`.

## Install

```bash
python -m pip install dbt-data-engineering-toolkit-compiler==3.2.0
```

The default installation includes Data Contract CLI, dbt Core, dbt-duckdb,
DuckDB, and SQLFluff. Install one additional warehouse adapter per deployment
environment, for example:

```bash
python -m pip install "dbt-data-engineering-toolkit-compiler[snowflake]"
```

Supported extras are `athena`, `bigquery`, `clickhouse`, `databricks`,
`duckdb`, `postgres`, `redshift`, `snowflake`, and `spark`.

## Safe first workbook

```bash
det workbook build data_product.xlsx --no-input
det validate data_product.xlsx
```

The default is blank: it does not add Customer 360 sample data. Use
`--sample-customer-data` only when you explicitly want the demonstration.

Continue with `det --help` and `det workbook --help`. The source repository's
root README contains the complete workbook-to-ODCS-to-dbt walkthrough,
architecture, compatibility matrix, testing definitions, and deployment guide.
