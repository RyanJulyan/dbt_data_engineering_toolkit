# Deploy V2.3.0 to PyPI and dbt Package Hub

V2.3.0 publishes three related artifacts:

| Artifact | Distribution | Consumer API |
| --- | --- | --- |
| canonical dbt package | immutable GitHub release, then dbt Package Hub | `dbt_data_engineering_toolkit.*` |
| short-name companion project | pinned Git subdirectory or separate Hub repository | `de_toolkit.*` |
| Python compiler | checked wheel and source distribution on PyPI with OIDC provenance | `det` |

Package Hub consumes `dbt/`. PyPI consumes only `python/`. The release workflow publishes both
from the same `v2.3.0` tag after the local quality gates pass.

## 1. Create the permanent public repository

Use the final public URL before releasing, for example:

```text
https://github.com/systemizing-solutions/dbt_data_engineering_toolkit
```

The `dbt/` subfolder must retain `dbt_project.yml`, `packages.yml`, `macros/`, `.sqlfluff`, and
`.sqlfluffignore`. The dbt project name must remain `dbt_data_engineering_toolkit`; dbt derives the
macro namespace from that name.

Confirm the release range and dependencies:

```yaml
require-dbt-version: [">=1.10.6", "<3.0.0"]
```

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.4.1
  - package: AxelThevenot/dbt_assertions
    version: 1.8.3
  - package: dbt-labs/codegen
    version: 0.14.1
  - package: dbt-labs/dbt_project_evaluator
    version: 1.3.5
```

Review dbt's [package-author guide](https://docs.getdbt.com/guides/building-packages) and
[Fusion package compatibility guide](https://docs.getdbt.com/guides/dbt-package-compat).

## 2. Configure warehouse integration credentials

Create repository Actions variables and secrets matching this table. Use dedicated CI users,
least-privilege credentials, disposable schemas, and warehouse cost controls.

| Platform | Actions variables | Actions secrets |
| --- | --- | --- |
| BigQuery | `BIGQUERY_PROJECT` | `BIGQUERY_KEYFILE_JSON` |
| Snowflake | `SNOWFLAKE_USER`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE` | `SNOWFLAKE_ACCOUNT`, `DBT_ENV_SECRET_SNOWFLAKE_PASS` |
| Databricks | `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH` | `DBT_ENV_SECRET_DATABRICKS_TOKEN` |
| Redshift | `REDSHIFT_HOST`, `REDSHIFT_PORT`, `REDSHIFT_USER`, `REDSHIFT_DATABASE` | `DBT_ENV_SECRET_REDSHIFT_PASS` |
| Athena | `ATHENA_DATABASE`, `ATHENA_REGION_NAME`, `ATHENA_S3_DATA_DIR`, `ATHENA_S3_DATA_NAMING`, `ATHENA_S3_STAGING_DIR` | `DBT_ENV_SECRET_ATHENA_AWS_ACCESS_KEY_ID`, `DBT_ENV_SECRET_ATHENA_AWS_SECRET_ACCESS_KEY` |
| Spark | `SPARK_HOST`, `SPARK_PORT`, `SPARK_USER`, `SPARK_METHOD` | adapter/authentication-specific secrets, if required by the selected method |
| ClickHouse | `DET_CLICKHOUSE_HOST`, `DET_CLICKHOUSE_PORT`, `DET_CLICKHOUSE_USER` | `DBT_ENV_SECRET_DET_CLICKHOUSE_PASSWORD` |

`.github/workflows/cloud-integration.yml` creates a unique schema for each run. It uses dbt Labs'
official `dbt-package-testing` Core and Fusion workflows for supported adapters and a dedicated
ClickHouse Core job. It is available as a manual release-candidate preflight and is also called by
the tag release workflow, so publication cannot proceed without its credentialed builds. Protect
the credentials from untrusted code and require review on the `pypi` environment.

## 3. Configure PyPI trusted publishing

In GitHub, create an environment named `pypi` and add a required reviewer. In PyPI, create either
the project or a pending trusted publisher with:

| Setting | Value |
| --- | --- |
| PyPI project | `dbt-data-engineering-toolkit-compiler` |
| GitHub owner | `systemizing-solutions` |
| Repository | `dbt_data_engineering_toolkit` |
| Workflow | `release.yml` |
| Environment | `pypi` |

The workflow requests a short-lived OpenID Connect token through `id-token: write`; do not store a
long-lived PyPI API token. PyPI documents the setup in its
[trusted publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## 4. Run every release gate

From a clean checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./python[test,release]"

python scripts/release.py verify-tag v2.3.0
python scripts/generate_alias_facade.py --check
python scripts/static_check.py
make quality
make python-coverage
make dbt-coverage
make codegen evaluator

det prove \
  python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx \
  --project-dir examples/compiler/customer_accounts \
  --local-package-root .
```

Expected coverage is at least 80% for both codebases. V2.3.0 records 85.01% Python statement
coverage, 98.53% (134/136) DuckDB-scoped dbt macro implementation coverage, and 100% (104/104)
public-API direct execution coverage. Read the exact metric definitions in [testing](testing.md).

Next run the credentialed matrix as a release-candidate preflight and wait for every job to pass:

```bash
gh workflow run cloud-integration.yml --repo systemizing-solutions/dbt_data_engineering_toolkit
gh run list --workflow cloud-integration.yml --limit 1 \
  --repo systemizing-solutions/dbt_data_engineering_toolkit
gh run watch RUN_ID --exit-status --repo systemizing-solutions/dbt_data_engineering_toolkit
```

Do not tag the release if a supported warehouse was skipped. The release workflow runs this
matrix again for the tagged commit and separately builds DuckDB with Fusion before it can build
or publish the distributions. Fusion cannot test Athena or ClickHouse until Fusion supplies those
adapters; their Core builds remain required. See the [compatibility matrix](compatibility.md).

## 5. Build and inspect the PyPI artifacts locally

```bash
python -m build python --outdir dist
python -m twine check dist/*
python -m zipfile --list dist/dbt_data_engineering_toolkit_compiler-2.3.0-py3-none-any.whl
```

The wheel must contain `py.typed`, `resources/operators.yml`, and all three controlled workbook
resources. Test the exact wheel in a clean environment:

```bash
python -m venv /tmp/det-wheel-smoke
/tmp/det-wheel-smoke/bin/python -m pip install \
  dist/dbt_data_engineering_toolkit_compiler-2.3.0-py3-none-any.whl
/tmp/det-wheel-smoke/bin/det --help
/tmp/det-wheel-smoke/bin/det workbook build /tmp/release-smoke.xlsx --no-input
/tmp/det-wheel-smoke/bin/det validate /tmp/release-smoke.xlsx
```

## 6. Push source and create the immutable release

For a new repository:

```bash
git init
git add .
git commit -m "Release dbt_data_engineering_toolkit v2.3.0"
git branch -M main
git remote add origin git@github.com:systemizing-solutions/dbt_data_engineering_toolkit.git
git push -u origin main

git tag -a v2.3.0 -m "dbt_data_engineering_toolkit v2.3.0"
git push origin v2.3.0
```

`.github/workflows/release.yml` repeats the release proof, requires the credentialed Core/Fusion
matrix and Fusion DuckDB build, builds and clean-installs both Python distribution formats, and
builds and extract-tests a Windows-safe source ZIP. It publishes the Python distributions to PyPI
with trusted publishing and attaches all release files to the GitHub release consumed by Package
Hub.

Verify both channels:

```bash
gh release view v2.3.0 --repo systemizing-solutions/dbt_data_engineering_toolkit
python -m pip index versions dbt-data-engineering-toolkit-compiler
```

Never move or overwrite a published tag. Correct a release with a new semantic version.

## 7. Smoke-test the Git dbt package

In a clean consumer project, create:

```yaml
packages:
  - git: "https://github.com/systemizing-solutions/dbt_data_engineering_toolkit.git"
    revision: v2.3.0
    subdirectory: dbt
  - git: "https://github.com/systemizing-solutions/dbt_data_engineering_toolkit.git"
    revision: v2.3.0
    subdirectory: aliases/de_toolkit
```

Then run:

```bash
dbt clean
dbt deps
dbt parse
dbt build
```

Compile at least one call through each namespace before submitting the package to Hub.

## 8. Submit the canonical package to dbt Package Hub

Follow the current [Hubcap README](https://github.com/dbt-labs/hubcap): fork Hubcap, add
`systemizing-solutions/dbt_data_engineering_toolkit` to `hub.json` in sorted order, and open a pull request.
Hubcap discovers semantic GitHub releases and opens the registry-data change used by Package Hub.

```bash
gh repo fork dbt-labs/hubcap --clone
cd hubcap
git checkout -b add-dbt-data-engineering-toolkit
# Add systemizing-solutions/dbt_data_engineering_toolkit to hub.json in sorted order.
git add hub.json
git commit -m "Add systemizing-solutions/dbt_data_engineering_toolkit"
git push -u origin add-dbt-data-engineering-toolkit
gh pr create --repo dbt-labs/hubcap \
  --title "Add systemizing-solutions/dbt_data_engineering_toolkit" \
  --body "Adds dbt_data_engineering_toolkit v2.3.0 to dbt Package Hub."
```

After Hub ingestion, verify the registry dependency:

```yaml
packages:
  - package: systemizing-solutions/dbt_data_engineering_toolkit
    version: 2.3.0
```

```bash
dbt clean
dbt deps
dbt build
```

The nested `de_toolkit` project is not automatically a second Hub package. Continue using the
pinned Git subdirectory entry, or publish that project from its own top-level repository. dbt has
no package-level Python-style alias.
