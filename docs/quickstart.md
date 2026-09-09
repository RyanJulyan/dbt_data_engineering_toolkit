# V4.0.3 quickstart

This creates a blank product, imports a schema, maps it, and produces a checked dbt project.

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./python"
```

The default install includes Data Contract CLI with Excel support, dbt Core, dbt-duckdb,
DuckDB, SQLFluff, and the dbt templater.

## 2. Build a safe workbook

```bash
det workbook build contracts/orders.xlsx --no-input \
  --product-id orders \
  --name "Orders" \
  --domain sales
```

No customer rows, sources, mappings, rules, or lookups are added. Demo content requires the
explicit `--sample-customer-data` flag.

## 3. Import an existing schema, if available

```bash
det workbook import contracts/imported_orders.xlsx --from-contract standard_odcs.xlsx
```

You can instead use ODCS YAML, SQL DDL, or a dbt `target/manifest.json`. For a workbook created in
step 2, use `det source import` to register upstream data and complete the output schema in Excel.

## 4. Complete the workbook

1. Set product identity and ownership in `Fundamentals`.
2. Define output fields in `Schema <model>`.
3. Add the model in `DET Models` and ordered inputs in `DET Model Inputs`.
4. Register physical inputs in `DET Sources` and `DET Source Schema`.
5. Add source-to-target operations in `DET Mapping` and `DET Parameters`.
6. Add key/value rows in `DET Lookups` where mappings need them.
7. Put contract rules in `Quality`.
8. Put warnings, quarantine, or runtime failure behavior in `Operational Validation` and
   `Operational Parameters`.

After structural edits:

```bash
det workbook refresh contracts/orders.xlsx
det validate contracts/orders.xlsx
```

## 5. Understand the generated SQL

Mappings compile to inline expressions, not a model-level dictionary:

{% raw %}
```sql
select
    {{ dbt_data_engineering_toolkit.clean_string('customer_name') }} as customer_name,
    {{ de_toolkit.mapping(
        expression='event_code',
        mapping={
            'launch': '2026-09-04',
            'renewal': '2027-01-15'
        },
        default='2026-01-01',
        data_type='date',
        format={'pattern': '%d/%m/%Y'}
    ) }} as event_date_display,
    {{ de_toolkit.is_email('email') }} as _email_valid
from {{ source('raw', 'customers') }}
```
{% endraw %}

Both namespaces are real dbt packages; no per-model Jinja alias is required.

## 6. Generate

```bash
det generate contracts/orders.xlsx --project-dir build/orders --dry-run --prune
det generate contracts/orders.xlsx --project-dir build/orders --prune
```

Generation creates ODCS and DET YAML, models, schema YAML, quarantine views, package/profile
configuration, `.sqlfluff`, a project README, and `.det-manifest.json`.

## 7. Install dbt packages and check

```bash
export DBT_DATA_ENGINEERING_TOOLKIT_GIT_URL=https://github.com/systemizing-solutions/dbt_data_engineering_toolkit.git
cd build/orders
dbt deps --profiles-dir .
cd ../..

det check contracts/orders.xlsx --project-dir build/orders
det prove contracts/orders.xlsx --project-dir build/orders
```

`dbt deps` creates `dbt_packages/` and normally creates or updates `package-lock.yml`. The dbt
manifest appears at `build/orders/target/manifest.json` after parse/build. DET's
`build/orders/.det-manifest.json` is a separate drift ledger.
