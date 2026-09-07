#!/usr/bin/env python3
"""Refresh release fixtures that must stay in lockstep with version bumps."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE = ROOT / "python" / "src"


def run_command(args: list[str]) -> None:
    env = dict(os.environ)
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{PYTHON_SOURCE}{os.pathsep}{pythonpath}"
        if pythonpath
        else str(PYTHON_SOURCE)
    )
    result = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    run_command(
        [
            sys.executable,
            "-m",
            "dbt_data_engineering_toolkit_compiler",
            "workbook",
            "refresh",
            "python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_sample.xlsx",
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "dbt_data_engineering_toolkit_compiler",
            "workbook",
            "refresh",
            "python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx",
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "dbt_data_engineering_toolkit_compiler",
            "generate",
            "python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_sample.xlsx",
            "--project-dir",
            "examples/compiler/customer_360",
            "--prune",
            "--force",
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "dbt_data_engineering_toolkit_compiler",
            "generate",
            "python/src/dbt_data_engineering_toolkit_compiler/resources/data_product_multi_source_sample.xlsx",
            "--project-dir",
            "examples/compiler/customer_accounts",
            "--prune",
            "--force",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())