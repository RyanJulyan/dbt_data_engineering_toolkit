"""Verify that a parsed manifest contains every critical adapter dispatch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PACKAGE = "dbt_data_engineering_toolkit"
CRITICAL_DISPATCHES = (
    "try_cast",
    "regex_match",
    "_det_regex_string",
    "format_temporal",
    "_det_grouped_number",
    "percentile",
    "_det_string_position",
    "normalize_whitespace",
    "regex_replace_all",
    "string_title",
    "string_split_part",
)
EXPLICIT_DISPATCHES = {
    "try_cast",
    "regex_match",
    "format_temporal",
    "_det_grouped_number",
    "percentile",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--adapter", required=True)
    args = parser.parse_args()

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    macros = payload.get("macros") or {}
    available = {
        value.get("name")
        for value in macros.values()
        if isinstance(value, dict) and value.get("package_name") == PACKAGE
    }
    missing: list[str] = []
    resolved: dict[str, str] = {}
    for dispatch in CRITICAL_DISPATCHES:
        adapter_name = f"{args.adapter}__{dispatch}"
        default_name = f"default__{dispatch}"
        if adapter_name in available:
            resolved[dispatch] = adapter_name
        elif dispatch not in EXPLICIT_DISPATCHES and default_name in available:
            resolved[dispatch] = default_name
        else:
            missing.append(dispatch)

    print(
        json.dumps(
            {
                "adapter": args.adapter,
                "critical_dispatches": len(CRITICAL_DISPATCHES),
                "resolved": resolved,
                "missing": missing,
            },
            indent=2,
        )
    )
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
