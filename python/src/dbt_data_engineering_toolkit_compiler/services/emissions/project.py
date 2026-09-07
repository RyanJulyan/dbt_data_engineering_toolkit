"""Composition of independently owned dbt-project artifact emitters."""

from __future__ import annotations

from pathlib import Path

from ...models import DataProductSpecification, FailureMode
from ...operational import Artifact
from ...registry import OperatorRegistry
from .common import GENERATED_HEADER_SQL
from .generated_readme import GeneratedReadmeEmitter
from .project_config import ProjectConfigurationEmitter
from .schema import ModelYamlEmitter, SourceYamlEmitter
from .sql import ModelSqlEmitter, SingularTestEmitter


class DbtProjectEmitter:
    def __init__(
        self,
        registry: OperatorRegistry | None = None,
        configuration: ProjectConfigurationEmitter | None = None,
        model_sql: ModelSqlEmitter | None = None,
        model_yaml: ModelYamlEmitter | None = None,
        source_yaml: SourceYamlEmitter | None = None,
        singular_test: SingularTestEmitter | None = None,
        readme: GeneratedReadmeEmitter | None = None,
    ) -> None:
        self.registry = registry or OperatorRegistry.load()
        self.configuration = configuration or ProjectConfigurationEmitter()
        self.model_sql = model_sql or ModelSqlEmitter()
        self.model_yaml = model_yaml or ModelYamlEmitter()
        self.source_yaml = source_yaml or SourceYamlEmitter()
        self.singular_test = singular_test or SingularTestEmitter()
        self.readme = readme or GeneratedReadmeEmitter()

    def emit(self, spec: DataProductSpecification) -> list[Artifact]:
        artifacts = self.configuration.emit(spec)
        artifacts.append(Artifact(Path("models/sources.yml"), self.source_yaml.emit(spec)))
        for model in spec.models:
            if not model.enabled:
                continue
            layer = "marts" if model.layer.value == "mart" else model.layer.value
            artifacts.extend(
                [
                    Artifact(
                        Path(f"models/{layer}/{model.name}.sql"),
                        self.model_sql.emit(spec, model, self.registry),
                    ),
                    Artifact(
                        Path(f"models/{layer}/{model.name}.yml"),
                        self.model_yaml.emit(spec, model, self.registry),
                    ),
                ]
            )
            if any(
                item.model == model.name and item.failure == FailureMode.REJECT
                for item in spec.rules
            ):
                artifacts.extend(self._quarantine(model.name))
        for rule in spec.rules:
            operator = self.registry.resolve(rule.operation)
            contract_native = operator is not None and operator.key in {
                "required",
                "unique",
            }
            if rule.failure == FailureMode.FAIL and not contract_native:
                artifacts.append(
                    Artifact(
                        Path(f"tests/{rule.model}__{rule.name}.sql"),
                        self.singular_test.emit(rule, self.registry),
                    )
                )
        artifacts.extend(
            [
                Artifact(Path("Makefile"), self._makefile()),
                Artifact(Path("README.md"), self.readme.emit(spec)),
            ]
        )
        return artifacts

    @staticmethod
    def _quarantine(model_name: str) -> list[Artifact]:
        return [
            Artifact(
                Path(f"models/quarantine/{model_name}_valid.sql"),
                GENERATED_HEADER_SQL
                + f"select *\nfrom {{{{ ref('{model_name}') }}}}\n"
                + "where {{ de_toolkit.keep_valid_rows(column='_det_rejections') }}\n",
            ),
            Artifact(
                Path(f"models/quarantine/{model_name}_rejected.sql"),
                GENERATED_HEADER_SQL
                + f"select *\nfrom {{{{ ref('{model_name}') }}}}\n"
                + "where {{ de_toolkit.keep_quarantined_rows(column='_det_rejections') }}\n",
            ),
        ]

    @staticmethod
    def _makefile() -> str:
        return """SHELL := /bin/sh

.PHONY: deps lint parse build evaluator

deps:
\tdbt deps --profiles-dir .

lint:
\tsqlfluff lint models tests --config .sqlfluff

parse:
\tdbt parse --profiles-dir .

build:
\tdbt build --profiles-dir . --exclude package:dbt_project_evaluator

evaluator:
\tdbt seed --profiles-dir . --select package:dbt_project_evaluator
\tdbt run --profiles-dir . --select package:dbt_project_evaluator
"""
