"""Shared paths and release metadata for structural checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DBT_ROOT = ROOT / "dbt"
ALIAS_ROOT = ROOT / "aliases" / "de_toolkit"
PYTHON_SOURCE = ROOT / "python" / "src"
if str(PYTHON_SOURCE) not in sys.path:
    sys.path.insert(0, str(PYTHON_SOURCE))

from dbt_data_engineering_toolkit_compiler.version import COMPILER_VERSION

__all__ = ["ALIAS_ROOT", "COMPILER_VERSION", "DBT_ROOT", "PYTHON_SOURCE", "ROOT"]
