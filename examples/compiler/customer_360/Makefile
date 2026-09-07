SHELL := /bin/sh

.PHONY: deps lint parse build evaluator

deps:
	dbt deps --profiles-dir .

lint:
	sqlfluff lint models tests --config .sqlfluff

parse:
	dbt parse --profiles-dir .

build:
	dbt build --profiles-dir . --exclude package:dbt_project_evaluator

evaluator:
	dbt seed --profiles-dir . --select package:dbt_project_evaluator
	dbt run --profiles-dir . --select package:dbt_project_evaluator
