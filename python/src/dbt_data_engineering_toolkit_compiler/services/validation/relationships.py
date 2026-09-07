"""Join-cardinality, connectivity, and model-cycle validation."""

from __future__ import annotations

from collections import defaultdict

from ...errors import DiagnosticCategory
from ...models import Cardinality, Relationship
from .common import validate_identifier
from .context import ValidationContext


class RelationshipValidator:
    def validate(self, context: ValidationContext) -> None:
        spec = context.spec
        by_model: dict[str, list[Relationship]] = defaultdict(list)
        for relationship in spec.relationships:
            by_model[relationship.model].append(relationship)
            if relationship.model not in context.model_names:
                context.add(
                    "DET-REL-001",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Relationships",
                    relationship.workbook_row,
                    f"unknown output model {relationship.model!r}",
                )
                continue
            model_inputs = set(spec.model(relationship.model).inputs)
            for relation in (
                relationship.left_relation,
                relationship.right_relation,
            ):
                if relation not in model_inputs:
                    context.add(
                        "DET-REL-002",
                        DiagnosticCategory.RELATIONSHIP,
                        "DET Relationships",
                        relationship.workbook_row,
                        f"{relation!r} is not an input to {relationship.model}",
                    )
            for relation, key in (
                (relationship.left_relation, relationship.left_key),
                (relationship.right_relation, relationship.right_key),
            ):
                validate_identifier(
                    context,
                    key,
                    "join key",
                    "DET Relationships",
                    relationship.workbook_row,
                    code="DET-REL-003",
                    category=DiagnosticCategory.RELATIONSHIP,
                )
                if key not in context.relation_fields.get(relation, {}):
                    available = sorted(context.relation_fields.get(relation, {}))
                    context.add(
                        "DET-REL-004",
                        DiagnosticCategory.RELATIONSHIP,
                        "DET Relationships",
                        relationship.workbook_row,
                        f"join key {relation}.{key} is not declared in that relation's schema",
                        (
                            "Choose one of: " + ", ".join(available) + "."
                            if available
                            else "Import or declare the relation schema, then refresh the workbook."
                        ),
                        model=relationship.model,
                        relation=relation,
                    )
            if relationship.left_relation == relationship.right_relation:
                context.add(
                    "DET-REL-005",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Relationships",
                    relationship.workbook_row,
                    "join relations must be different",
                )
            if (
                relationship.cardinality == Cardinality.MANY_TO_MANY
                and not spec.build.allow_many_to_many
            ):
                context.add(
                    "DET-REL-006",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Relationships",
                    relationship.workbook_row,
                    "many-to-many join is blocked because it can multiply rows",
                )

        for model in spec.models:
            relationships = by_model[model.name]
            if len(model.inputs) <= 1:
                if relationships:
                    context.add(
                        "DET-REL-007",
                        DiagnosticCategory.RELATIONSHIP,
                        "DET Relationships",
                        relationships[0].workbook_row,
                        f"{model.name} has one input and must not define a join",
                    )
                continue
            if len(relationships) != len(model.inputs) - 1:
                context.add(
                    "DET-REL-008",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Relationships",
                    None,
                    f"{model.name} needs {len(model.inputs) - 1} ordered relationship rows for {len(model.inputs)} inputs",
                )
                continue
            connected = {relationships[0].left_relation}
            for relationship in relationships:
                if relationship.left_relation not in connected:
                    context.add(
                        "DET-REL-009",
                        DiagnosticCategory.RELATIONSHIP,
                        "DET Relationships",
                        relationship.workbook_row,
                        f"{relationship.left_relation!r} is not connected by an earlier relationship",
                    )
                connected.update((relationship.left_relation, relationship.right_relation))
            if connected != set(model.inputs):
                context.add(
                    "DET-REL-010",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Relationships",
                    None,
                    f"{model.name} relationships do not connect exactly its inputs",
                )
        self._validate_model_cycles(context)

    @staticmethod
    def _validate_model_cycles(context: ValidationContext) -> None:
        spec = context.spec
        graph = {
            item.name: [
                input_name for input_name in item.inputs if input_name in context.model_names
            ]
            for item in spec.models
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str, path: list[str]) -> None:
            if node in visiting:
                start = path.index(node)
                cycle = path[start:] + [node]
                context.add(
                    "DET-REL-011",
                    DiagnosticCategory.RELATIONSHIP,
                    "DET Models",
                    None,
                    f"model dependency cycle: {' -> '.join(cycle)}",
                    "Remove one circular input reference.",
                )
                return
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph.get(node, []):
                visit(dependency, [*path, node])
            visiting.remove(node)
            visited.add(node)

        for name in graph:
            visit(name, [])
