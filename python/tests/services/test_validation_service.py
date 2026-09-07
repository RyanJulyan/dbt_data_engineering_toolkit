"""Focused tests for validation-service composition and diagnostics."""

import pytest

from dbt_data_engineering_toolkit_compiler.errors import (
    DiagnosticCategory,
    SpecificationValidationError,
)
from dbt_data_engineering_toolkit_compiler.models import (
    DataProductSpecification,
    ProductMetadata,
)
from dbt_data_engineering_toolkit_compiler.services.validation.context import (
    ValidationContext,
)
from dbt_data_engineering_toolkit_compiler.services.validation.service import (
    SpecificationValidationService,
)


class RejectingValidator:
    def validate(self, context: ValidationContext) -> None:
        context.add(
            "DET-TST-001",
            DiagnosticCategory.WORKBOOK,
            "Workbook",
            None,
            "test failure",
            "fix the test input",
        )


def test_service_aggregates_stable_diagnostics_from_injected_validators() -> None:
    specification = DataProductSpecification(
        metadata=ProductMetadata(product_id="product", name="Product")
    )
    service = SpecificationValidationService(validators=(RejectingValidator(),))

    with pytest.raises(SpecificationValidationError) as raised:
        service.validate(specification)

    rendered = str(raised.value)
    assert "DET-TST-001" in rendered
    assert "fix the test input" in rendered
