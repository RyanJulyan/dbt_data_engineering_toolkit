"""Tests for the technology-neutral workbook broker boundary."""

from pathlib import Path

import pytest

from dbt_data_engineering_toolkit_compiler.brokers.workbooks import WorkbookDocument
from dbt_data_engineering_toolkit_compiler.errors import SpecificationValidationError
from dbt_data_engineering_toolkit_compiler.services.workbooks.service import (
    WorkbookInterpretationService,
)


class EmptyWorkbookBroker:
    def read(self, path: Path) -> WorkbookDocument:
        del path
        return WorkbookDocument(sheets={})


def test_interpreter_reports_stable_codes_without_openpyxl() -> None:
    service = WorkbookInterpretationService(workbook_broker=EmptyWorkbookBroker())

    with pytest.raises(SpecificationValidationError) as raised:
        service.load(Path("product.xlsx"))

    assert "DET-WBK-002" in str(raised.value)
    assert "missing required sheet" in str(raised.value)
