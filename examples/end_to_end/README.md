# End-to-end inline example

The package root [README](../../README.md) contains the complete numbered
walkthrough, every file's contents, explanations, and expected output. This is
the short run sheet for the included project. The staging model uses direct
expression macros throughout; there is no cleaning configuration dictionary.
The example installs both project roots and exercises both the canonical
`dbt_data_engineering_toolkit.*` and short `de_toolkit.*` namespaces.

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "../../python"

export DBT_DATA_ENGINEERING_TOOLKIT_GIT_URL=https://github.com/YOUR_ORG/dbt_data_engineering_toolkit.git
dbt deps --profiles-dir .
dbt debug --profiles-dir .
sqlfluff lint . --config .sqlfluff
dbt build --profiles-dir . --exclude package:dbt_project_evaluator
dbt show --profiles-dir . --select stg_customer_events --limit 10
dbt show --profiles-dir . --select stg_customer_events_rejected --limit 10
dbt docs generate --profiles-dir .

dbt seed --profiles-dir . --select package:dbt_project_evaluator
dbt run --profiles-dir . --select package:dbt_project_evaluator
dbt test --profiles-dir . --select package:dbt_project_evaluator
```

Expected pipeline result:

| Relation | Rows |
| --- | ---: |
| `stg_customer_events` | 3 |
| `stg_customer_events_valid` | 2 |
| `stg_customer_events_rejected` | 1 |

The ordinary build reports `PASS=8 WARN=0 ERROR=0 TOTAL=8`. The evaluator gate
reports `PASS=26 WARN=3 ERROR=0 TOTAL=29`; the root README explains those three
intentional findings.
