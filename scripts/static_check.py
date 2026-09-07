#!/usr/bin/env python3
"""Run independently owned structural checks."""

from __future__ import annotations

from checks.facade import check_facade
from checks.paths import ALIAS_ROOT, ROOT
from checks.project import check_project
from checks.syntax import check_jinja, check_yaml
from checks.workbook import check_workbooks


def main() -> int:
    errors = (
        check_yaml()
        + check_jinja()
        + check_project()
        + check_facade()
        + check_workbooks()
    )
    if errors:
        print("Static checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    core_count = len(list((ROOT / "dbt" / "macros").rglob("*.sql")))
    alias_count = len(list((ALIAS_ROOT / "macros").rglob("*.sql")))
    print(
        f"Static checks passed ({core_count} canonical and {alias_count} alias SQL macro files)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
