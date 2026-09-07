# dbt_data_engineering_toolkit

**From shared data-product definition to production dbt.**

Bridge the gap between business requirements and production dbt with shared data-product definitions, source-to-target mappings, validation, reusable engineering macros, and deterministic dbt generation. With an ODCS Excel-template superset Data Contract first approach that compiles to an inline-first dbt package for routine data-engineering work

`dbt_data_engineering_toolkit` helps **BAs, analysts and data engineers work from the same data-product specification**, validate engineering intent before implementation, and turn that specification into **consistent, readable and testable dbt**.

Instead of allowing requirements, source-to-target mappings, transformation logic, data contracts and implementation decisions to drift across spreadsheets, tickets, documentation and code, the toolkit creates one structured path:

```text
Business Requirements
        ↓
Shared Data Product Definition
        ↓
Source-to-Target Mapping
        ↓
Transformations + Quality Rules
        ↓
Validate Early
        ↓
Generate dbt
        ↓
dbt build / test / prove
```

> **The specification becomes the collaboration point.**
>
> BAs and analysts can help define **what the data product should do**, while data engineers retain control over **how it is implemented**.

The generated result is still ordinary, readable dbt. There is no proprietary runtime and no requirement to understand the workbook or compiler to understand the resulting project.

---

## Why this exists

The path from a business requirement to a production dbt data product often becomes fragmented across:

* requirements and tickets
* source-to-target mapping spreadsheets
* data contracts
* transformation specifications
* validation rules
* dbt models and tests
* engineer- or team-specific implementation patterns

The individual artefacts may all be reasonable, but keeping them aligned becomes increasingly difficult.

The same common engineering tasks also tend to be implemented slightly differently from project to project:

* How do we clean a string?
* How do we standardise a country?
* How do we validate an email?
* How do we map business values?
* What happens to an invalid row?
* How do we express source-to-target intent?
* How do we prove the implementation still matches the contract?

`dbt_data_engineering_toolkit` addresses both problems:

1. **Create a shared definition of the data product before implementation.**
2. **Provide a standard engineering vocabulary for implementing it.**

---

# Two complementary toolkits

The repository contains two closely related components.

## 🧱 Reusable dbt package

The dbt package provides an **inline-first engineering vocabulary** for routine data-engineering work:

```text
clean
  → standardize
  → map
  → convert
  → format
  → validate
  → assert
  → quarantine
  → document
  → evaluate
```

Common operations are expressed as normal SQL-expression macros and remain beside the fields they affect.

For example:

```sql
select
    {{ de_toolkit.clean_string('customer_name') }} as customer_name,
    {{ de_toolkit.clean_email('email') }} as email,
    {{ de_toolkit.clean_numeric(
        'revenue',
        precision=18,
        scale=2
    ) }} as revenue
from {{ source('raw', 'customers') }}
```

Common macros include:

```text
clean_string()
clean_email()
clean_phone()
clean_numeric()
clean_date()
clean_timestamp()
clean_boolean()

standardize_country()
standardize_currency()

mapping()
fill_missing()

is_email()
is_positive()
...
```

The API is deliberately **SQL-first**.

There is no model-level transformation dictionary to decode. A generated or handwritten model should remain readable from top to bottom as normal dbt.

### Two supported namespaces

The canonical package namespace is:

```jinja
dbt_data_engineering_toolkit.clean_string(...)
```

A shorter companion namespace is also available:

```jinja
de_toolkit.clean_string(...)
```

The `de_toolkit` package is only a thin facade over the canonical implementation, so the two APIs cannot develop separate behaviour.

The package also delegates established primitives to existing dbt ecosystem packages where appropriate, including:

* `dbt_utils`
* `dbt_assertions`
* `codegen`
* `dbt_project_evaluator`

Those implementation details do not need to leak into normal transformation models.

---

## 🐍 Data-product compiler and CLI

The Python package provides the `det` command-line interface.

It gives teams a controlled way to define a data product using:

* the DET Excel workbook
* ODCS contracts
* standard ODCS Excel
* SQL DDL
* dbt manifests

The controlled workbook uses **business-friendly names for common dbt and data-engineering concepts**, while retaining enough structure for deterministic compilation.

It captures:

* target schemas and fields
* upstream sources and their schemas
* source-to-target mappings
* ordered transformation steps
* joins
* expected join cardinality
* lookups
* model grain
* materialisation
* contract enforcement
* data-quality requirements
* operational validation
* warn / reject / quarantine / fail behaviour
* ownership
* support
* SLA and other contract metadata

The compiler then validates those decisions before generating:

* canonical ODCS 3.1 contracts
* DET execution metadata
* dbt sources
* dbt models
* model contracts
* tests
* quarantine models
* project configuration
* proof infrastructure

The generated project remains a normal dbt project.

---

# The collaboration model

This is the most important part of the toolkit.

The workbook is **not intended to turn analysts into dbt developers**, and the compiler is **not intended to replace data engineers**.

Instead, it creates a more useful boundary between roles.

### BAs and analysts can contribute to

* business definitions
* output fields
* source-to-target mappings
* transformation intent
* lookup values
* quality expectations
* ownership and support metadata

### Data engineers retain control over

* source structures
* data types
* model architecture
* joins
* grain
* cardinality
* transformation implementation
* operational validation
* materialisation
* generated code
* dbt execution
* deployment and review

The result is a specification that both groups can understand without forcing either group to work entirely in the other's abstraction.

And because the specification generates the implementation, **documentation and code can be kept aligned rather than maintained independently**.

---

# Quick start

## 1. Install the compiler

Requires Python 3.11+.

```bash
python -m venv .venv-compiler
source .venv-compiler/bin/activate

python -m pip install -e "./python"
```

The compiler installation includes its required dbt, Data Contract and SQLFluff dependencies.

---

## 2. Create a data-product workbook

```bash
det workbook build orders_data_product.xlsx
```

For non-interactive use:

```bash
det workbook build orders_data_product.xlsx \
  --no-input \
  --product-id orders_data_product \
  --name "Orders Data Product" \
  --domain sales \
  --owner "Sales Analytics"
```

The default workbook is intentionally safe and does not create example sources, mappings, rules or sample data.

---

## 3. Or start from an existing structure

You do not need to re-enter an existing schema manually.

### ODCS YAML

```bash
det workbook import orders.xlsx \
  --from-contract orders.odcs.yaml
```

### Standard ODCS Excel

```bash
det workbook import orders.xlsx \
  --from-contract standard_odcs.xlsx
```

### SQL DDL

```bash
det workbook import orders.xlsx \
  --from-ddl orders.sql
```

### dbt manifest

```bash
det workbook import orders.xlsx \
  --from-dbt-manifest upstream/target/manifest.json
```

Imported structures are intentionally not assumed to be transformation mappings.

If the structure really represents a one-to-one source, identity mappings can be requested explicitly:

```bash
det workbook import orders.xlsx \
  --from-ddl orders.sql \
  --identity-mappings
```

---

## 4. Define the data product

The workbook separates **what the product promises** from **how dbt implements it**.

### ODCS / contract surfaces

Examples include:

```text
Fundamentals
Schema <model>
Relationships
Quality
SLA
Servers
Team
Roles
Support
Pricing
Custom Properties
```

### DET implementation surfaces

Examples include:

```text
DET Models
DET Model Inputs
DET Sources
DET Source Schema
DET Mapping
DET Parameters
DET Lookups
DET Relationships
Operational Validation
Operational Parameters
DET Build
```

This allows business-facing contract information and engineering implementation information to coexist without becoming the same thing.

---

# Source-to-target mapping

Mappings remain deliberately compact.

A mapping identifies:

```text
Model
Target Field
Source Relation
Source Field
Step
Operation
```

For example:

| Model           | Target Field   | Source Relation | Source Field    | Step | Operation             |
| --------------- | -------------- | --------------- | --------------- | ---: | --------------------- |
| `stg_customers` | `email`        | `crm_customers` | `email_address` |    1 | `Clean email`         |
| `stg_customers` | `country_code` | `crm_customers` | `country`       |    1 | `Standardize country` |

Operation-specific configuration lives separately in `DET Parameters`, rather than turning the mapping sheet into a huge configuration form.

Multiple operations can be chained against the same target field using ordered steps.

---

# Multi-source products and joins

Models explicitly declare their input relations.

For example:

| Model               | Order | Input Relation     |
| ------------------- | ----: | ------------------ |
| `customer_accounts` |     1 | `crm_customers`    |
| `customer_accounts` |     2 | `billing_accounts` |

Relationships are also explicit.

The compiler validates:

* relation existence
* join keys
* model inputs
* dependency cycles
* grain
* source usage
* expected cardinality

Unsafe many-to-many joins can therefore be surfaced **before generated dbt reaches production**.

Declared cardinality can also result in generated uniqueness tests where one side of the relationship is expected to be unique.

---

# Data quality and operational behaviour

The toolkit separates two related concerns.

## Contract quality

Business-facing data-quality expectations belong in the ODCS `Quality` surface.

These describe what the data product promises.

Supported rule forms include:

* library rules
* SQL rules
* custom rules
* text rules

Schema constraints such as required, primary-key and uniqueness expectations remain part of the data contract rather than being duplicated in a competing DET format.

## Operational validation

Runtime row-handling behaviour belongs in `Operational Validation`.

A rule can explicitly define what should happen when validation fails:

| Failure behaviour | Result                                         |
| ----------------- | ---------------------------------------------- |
| `Allow`           | Document the rule and continue                 |
| `Warn`            | Add the rule to `_det_warnings`                |
| `Reject row`      | Route the row into rejection/quarantine output |
| `Fail build`      | Generate a failing dbt test                    |

This makes quality expectations and operational consequences explicit rather than burying them inside SQL.

---

# Validate before generating

Before generating anything:

```bash
det validate orders_data_product.xlsx
```

Validation checks include:

* identifiers
* source fields
* target fields
* model inputs
* source-to-target mappings
* operation parameters
* lookup names
* type flow
* target compatibility
* model grain
* dependency cycles
* duplicate mappings
* duplicate rules
* published-field implementation
* join keys
* join cardinality
* ODCS quality vocabulary

Errors identify the relevant workbook location and explain what needs to be corrected.

This is one of the primary goals of the toolkit:

> **Move implementation problems left — into the specification — instead of discovering them during or after dbt development.**

---

# Preview before changing generated code

Inspect the current state:

```bash
det status orders_data_product.xlsx \
  --project-dir build/orders
```

Preview generation:

```bash
det generate orders_data_product.xlsx \
  --project-dir build/orders \
  --dry-run \
  --prune
```

Then publish:

```bash
det generate orders_data_product.xlsx \
  --project-dir build/orders \
  --prune
```

Generation is deterministic.

No timestamps are written into generated files.

---

# Generated dbt is still dbt

A generated project contains ordinary files such as:

```text
contracts/
    orders_data_product.odcs.yaml
    orders_data_product.det.yaml

models/
    sources.yml

    staging/
        stg_orders.sql
        stg_orders.yml

    quarantine/
        stg_orders_valid.sql
        stg_orders_rejected.sql

tests/
    datacontract_cli/

dbt_project.yml
packages.yml
profiles.yml
.sqlfluff
.sqlfluffignore
Makefile
README.md
.det-manifest.json
```

The workbook and compiler are not required to understand the generated SQL.

For example, generated transformations remain explicit:

```sql
select
    {{ de_toolkit.clean_string('customer_name') }} as customer_name,
    {{ de_toolkit.clean_email('email') }} as email,
    {{ de_toolkit.standardize_country('country') }} as country_code
from {{ source('crm', 'customers') }}
```

This is intentional.

The toolkit generates **dbt**, rather than creating a second runtime abstraction that happens to execute SQL.

---

# Deterministic generation and drift protection

Generated files are tracked in `.det-manifest.json`.

The manifest records information such as:

* generated file hashes
* workbook hash
* compiler version
* workbook version
* operator registry version
* ODCS version
* adapter
* ownership of generated artefacts

A later generation refuses to silently overwrite hand-edited generated files.

That means changes have a clear home:

| Change                | Authoritative location           |
| --------------------- | -------------------------------- |
| Business contract     | Workbook / ODCS                  |
| Source definition     | Workbook or imported source      |
| Mapping               | Workbook                         |
| Transformation intent | Workbook                         |
| Quality rules         | Workbook / ODCS                  |
| Operational behaviour | Workbook                         |
| Compiler behaviour    | Toolkit source                   |
| Custom downstream SQL | Separate non-generated dbt model |

Generated files should not become another independently maintained source of truth.

---

# Atomic generation

Generation uses a staged transaction:

```text
workbook
    ↓
typed specification
    ↓
staged ODCS + DET + dbt
    ↓
Data Contract synchronization
    ↓
synchronized validation
    ↓
final hashes
    ↓
atomic publish
```

If synchronization, linting or synchronized-output validation fails, the existing generated project and its manifest are left untouched.

This prevents a failed generation from leaving a half-updated project behind.

---

# Check the generated product

Run the fast verification gates:

```bash
det check orders_data_product.xlsx \
  --project-dir build/orders
```

`det check` verifies the generated product using the appropriate tooling, including:

* ODCS validation
* Data Contract synchronization checks
* dbt parsing
* SQLFluff with the dbt templater

To run only the SQL lint gate:

```bash
det lint --project-dir build/orders
```

---

# Prove the generated product

For the full integration proof:

```bash
det prove orders_data_product.xlsx \
  --project-dir build/orders
```

Proof runs against a disposable copy of the generated project and can include:

```text
dependency installation
        ↓
Data Contract synchronization
        ↓
source fixtures
        ↓
dbt parse
        ↓
dbt build
        ↓
synchronized tests
        ↓
SQLFluff
        ↓
dbt_project_evaluator
```

The original generated project remains unchanged.

---

# Import and synchronization

Existing upstream structures can be imported from:

* ODCS YAML
* standard ODCS Excel
* SQL DDL
* dbt manifests

For example:

```bash
det source import \
  --workbook orders_data_product.xlsx \
  --from-dbt-manifest /path/to/upstream/target/manifest.json \
  --replace
```

Or:

```bash
det source import \
  --workbook orders_data_product.xlsx \
  --from-ddl raw_customers.sql \
  --relation crm_customers \
  --source-name raw \
  --replace
```

When an upstream contract changes, merge it without destroying mapping work:

```bash
det workbook sync contracts/orders_data_product.xlsx \
  --from-contract upstream_orders.odcs.yaml
```

Existing mapping, parameter, lookup and operational-validation decisions remain intact by default.

Any resulting incompatibility is surfaced through validation instead of being silently deleted.

---

# Supported adapters

The toolkit supports configuration for:

* BigQuery
* Snowflake
* DuckDB
* Databricks
* Redshift
* Athena
* ClickHouse
* Spark
* PostgreSQL

DuckDB is available for local execution and proof without external warehouse credentials.

Other generated profiles use environment-variable references rather than embedding credentials.

The exact dbt Core, Fusion and warehouse proof level differs by adapter. See:

* [Compatibility](docs/compatibility.md)
* [Testing](docs/testing.md)

---

# Release quality

Current release gates include:

| Gate                                      | Result |
| ----------------------------------------- | -----: |
| Python statement coverage                 | 85.01% |
| dbt DuckDB-scoped implementation coverage | 98.53% |
| dbt public-API direct execution coverage  |   100% |

Release gates fail below 80%.

For the exact coverage definitions, commands and warehouse matrix, see [Testing](docs/testing.md).

---

# Architecture

The public dbt API and compiler are intentionally separated.

```text
CLI / future API
       ↓
ToolkitApplication
       ↓
workbook
import
validation
emission
proof services
       ↓
file
workbook
dbt
SQLFluff
Data Contract
brokers
```

External libraries and commands are confined to broker boundaries.

The compiler operates on typed structures rather than passing workbook rows directly through the application.

Validation and emission are also separated:

```text
input
  ↓
typed specification
  ↓
validators
  ↓
validated specification
  ↓
emitters
  ↓
artifacts
```

For the full design, see [Architecture](docs/architecture.md).

---

# Documentation

| Need                                      | Guide                                           |
| ----------------------------------------- | ----------------------------------------------- |
| Fastest runnable path                     | [Quickstart](docs/quickstart.md)                |
| Full CLI reference                        | [CLI reference](docs/cli.md)                    |
| ODCS, DDL and dbt imports                 | [Import and synchronization](docs/imports.md)   |
| Workbook changes and generated-code drift | [Updating safely](docs/updating.md)             |
| Compiler architecture                     | [Architecture](docs/architecture.md)            |
| Adapter and Fusion support                | [Compatibility](docs/compatibility.md)          |
| Coverage and release gates                | [Testing](docs/testing.md)                      |
| Publishing and Package Hub                | [Deployment](docs/deployment.md)                |
| dbt-only usage and macro recipes          | [SQL walkthrough](docs/sql_walkthrough.md)      |
| Release details                           | [V2.3.0 release notes](V2.3.0_RELEASE_NOTES.md) |

---

# Installing the dbt package

Before publication to dbt Package Hub, install the package from Git:

```yaml
packages:
  - git: "https://github.com/YOUR_ORG/dbt_data_engineering_toolkit.git"
    revision: v2.3.0
```

To also use the short `de_toolkit` namespace:

```yaml
packages:
  - git: "https://github.com/YOUR_ORG/dbt_data_engineering_toolkit.git"
    revision: v2.3.0

  - git: "https://github.com/YOUR_ORG/dbt_data_engineering_toolkit.git"
    revision: v2.3.0
    subdirectory: aliases/de_toolkit
```

The short namespace is a separate thin dbt project because dbt does not provide Python-style package aliases.

---

# Development

Install development dependencies:

```bash
python -m pip install -e "./python[test]"
```

Run the project gates:

```bash
python scripts/generate_alias_facade.py --check
python scripts/static_check.py

make quality
make python-coverage
make dbt-coverage
make codegen evaluator
```

The current release supports dbt Core `1.10.6+` and declares the Fusion-compatible range:

```text
>=1.10.6,<3.0.0
```

---

# The goal

The broader goal is deliberately simple:

> **Define a data product once, make the engineering intent explicit, validate it early, and turn it into consistent, readable and testable dbt.**

Not another proprietary data platform.

Not another configuration language that hides the SQL.

Not another mapping spreadsheet that drifts away from the implementation.

A shared specification that creates a cleaner collaboration point between **BAs, analysts and data engineers**, backed by reusable engineering primitives and an implementation that remains recognisably **dbt**.
