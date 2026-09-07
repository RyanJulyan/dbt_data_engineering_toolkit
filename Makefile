.PHONY: deps parse build dbt-coverage codegen evaluator docs facade quality python-coverage compiler-test compiler-example compiler-proof lint release-archive check

deps:
	cd integration_tests && dbt deps --profiles-dir .

parse: deps
	cd integration_tests && dbt parse --profiles-dir .

build: deps
	cd integration_tests && dbt build --profiles-dir . --exclude package:dbt_project_evaluator

dbt-coverage: build
	python scripts/dbt_coverage.py --manifest integration_tests/target/manifest.json --run-results integration_tests/target/run_results.json --public-api macros/schema.yml --minimum 80 --output integration_tests/target/dbt_coverage.json

codegen: build
	cd integration_tests && dbt run-operation generate_model_yaml --profiles-dir . --args '{model_names: [stg_customers, stg_namespace_aliases, stg_cleaning_operations, stg_key_value_mapping]}'

evaluator: build
	cd integration_tests && dbt seed --profiles-dir . --select package:dbt_project_evaluator
	cd integration_tests && dbt run --profiles-dir . --select package:dbt_project_evaluator

docs: deps
	cd integration_tests && dbt docs generate --profiles-dir .

facade:
	python scripts/generate_alias_facade.py

quality:
	cd python && ruff check src tests
	cd python && ruff format --check src tests
	cd python && pyright

compiler-test:
	cd python && PYTHONPATH=src python -m pytest tests

python-coverage:
	PYTHONPATH=python/src python -m pytest python/tests --cov=dbt_data_engineering_toolkit_compiler --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=80

compiler-example:
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler validate python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_sample.xlsx
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler generate python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_sample.xlsx --project-dir examples/compiler/customer_360 --dry-run --prune
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler validate python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler generate python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx --project-dir examples/compiler/customer_accounts --dry-run --prune

compiler-proof:
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler check python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx --project-dir examples/compiler/customer_accounts --skip-dbt --skip-sqlfluff
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler prove python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx --project-dir examples/compiler/customer_accounts --local-package-root .

lint:
	PYTHONPATH=python/src python -m dbt_data_engineering_toolkit_compiler lint --project-dir examples/compiler/customer_360

release-archive:
	python scripts/build_source_archive.py

check:
	python scripts/generate_alias_facade.py --check
	python scripts/static_check.py
	$(MAKE) quality
	$(MAKE) python-coverage
	$(MAKE) compiler-example
	$(MAKE) compiler-proof
	$(MAKE) dbt-coverage
	$(MAKE) codegen
	$(MAKE) evaluator
