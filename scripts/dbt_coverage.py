"""Enforce adapter-scoped implementation and public-API coverage for dbt macros.

dbt does not publish line-level coverage data for Jinja. This gate discovers macro
definitions from source, follows the manifest dependency graph from successful
nodes, and measures the generic/private implementation plus the implementation
selected for the manifest's adapter. It separately requires every public facade
to be documented and directly exercised.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

PACKAGE_NAME = "dbt_data_engineering_toolkit"
PASSING_STATUSES = {"pass", "success", "warn"}
ADAPTER_PREFIXES = {
    "athena",
    "bigquery",
    "clickhouse",
    "databricks",
    "default",
    "duckdb",
    "postgres",
    "redshift",
    "snowflake",
    "spark",
}
MACRO_PATTERN = re.compile(r"\{%[-+]?\s*macro\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-results", type=Path, required=True)
    parser.add_argument("--public-api", type=Path, default=Path("macros/schema.yml"))
    parser.add_argument("--macros-dir", type=Path, default=Path("macros"))
    parser.add_argument("--minimum", type=float, default=80.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _documented_macros(path: Path) -> set[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    macros = payload.get("macros") or []
    names = [item.get("name") for item in macros if isinstance(item, dict)]
    if not names or any(not isinstance(name, str) or not name for name in names):
        raise ValueError(f"{path} must document at least one named public macro")
    if len(names) != len(set(names)):
        raise ValueError(f"{path} contains duplicate public macro names")
    return set(names)


def _source_macros(path: Path) -> set[str]:
    names: set[str] = set()
    for macro_path in sorted(path.rglob("*.sql")):
        names.update(MACRO_PATTERN.findall(macro_path.read_text(encoding="utf-8")))
    if not names:
        raise ValueError(f"{path} contains no macros")
    return names


def _source_public_macros(path: Path) -> set[str]:
    """Discover the same public surface exposed by the generated alias package."""

    return {
        name
        for name in _source_macros(path)
        if not name.startswith("_") and "__" not in name
    }


def _variant(name: str) -> tuple[str | None, str]:
    if "__" not in name:
        return None, name
    prefix, base = name.split("__", 1)
    return (prefix, base) if prefix in ADAPTER_PREFIXES else (None, name)


def _adapter_scope(definitions: set[str], adapter: str) -> set[str]:
    """Select generic code plus the dispatch branch reachable for one adapter."""

    target_bases = {
        base
        for name in definitions
        for prefix, base in [_variant(name)]
        if prefix == adapter
    }
    scoped: set[str] = set()
    for name in definitions:
        prefix, base = _variant(name)
        if (
            prefix is None
            or prefix == adapter
            or (prefix == "default" and base not in target_bases)
        ):
            scoped.add(name)
    return scoped


def _macro_dependencies(node: dict[str, object]) -> list[str]:
    dependencies = node.get("depends_on") or {}
    if not isinstance(dependencies, dict):
        return []
    macro_ids = dependencies.get("macros") or []
    return [item for item in macro_ids if isinstance(item, str)]


def coverage_report(
    manifest_path: Path,
    run_results_path: Path,
    public_api_path: Path,
    macros_dir: Path,
) -> dict[str, object]:
    """Calculate target-scoped implementation and public facade coverage."""

    manifest = _load_json(manifest_path)
    run_results = _load_json(run_results_path)
    nodes = manifest.get("nodes") or {}
    results = run_results.get("results") or []
    successful_ids = {
        item.get("unique_id")
        for item in results
        if isinstance(item, dict) and item.get("status") in PASSING_STATUSES
    }

    prefix = f"macro.{PACKAGE_NAME}."
    direct_ids: set[str] = set()
    if isinstance(nodes, dict):
        for unique_id in successful_ids:
            node = nodes.get(unique_id)
            if not isinstance(node, dict):
                continue
            direct_ids.update(
                macro_id
                for macro_id in _macro_dependencies(node)
                if macro_id.startswith(prefix)
            )

    manifest_macros = manifest.get("macros") or {}
    if not isinstance(manifest_macros, dict):
        raise TypeError(f"{manifest_path} has no macro mapping")
    covered_ids: set[str] = set()
    pending = list(direct_ids)
    while pending:
        macro_id = pending.pop()
        if macro_id in covered_ids:
            continue
        covered_ids.add(macro_id)
        macro = manifest_macros.get(macro_id)
        if isinstance(macro, dict):
            pending.extend(
                dependency
                for dependency in _macro_dependencies(macro)
                if dependency.startswith(prefix) and dependency not in covered_ids
            )

    direct_names = {macro_id.removeprefix(prefix) for macro_id in direct_ids}
    covered_names = {macro_id.removeprefix(prefix) for macro_id in covered_ids}

    public = _source_public_macros(macros_dir)
    documented = _documented_macros(public_api_path)
    if public != documented:
        undocumented = sorted(public - documented)
        unknown = sorted(documented - public)
        raise ValueError(
            f"{public_api_path} must document the complete public macro API; "
            f"undocumented={undocumented}, unknown={unknown}"
        )
    covered_public = public & direct_names
    missing = public - covered_public
    public_percent = round((len(covered_public) / len(public)) * 100, 2)

    metadata = manifest.get("metadata") or {}
    adapter = metadata.get("adapter_type") if isinstance(metadata, dict) else None
    if not isinstance(adapter, str) or not adapter:
        raise ValueError(f"{manifest_path} metadata must identify adapter_type")
    definitions = _source_macros(macros_dir)
    scoped = _adapter_scope(definitions, adapter)
    covered_implementation = scoped & covered_names
    missing_implementation = scoped - covered_implementation
    implementation_percent = round(
        (len(covered_implementation) / len(scoped)) * 100,
        2,
    )
    return {
        "metric": "adapter-scoped dbt macro implementation execution coverage",
        "package": PACKAGE_NAME,
        "adapter": adapter,
        "covered": len(covered_implementation),
        "total": len(scoped),
        "percent": implementation_percent,
        "covered_macros": sorted(covered_implementation),
        "missing_macros": sorted(missing_implementation),
        "public_api": {
            "metric": "source-derived public macro direct execution coverage",
            "covered": len(covered_public),
            "total": len(public),
            "percent": public_percent,
            "covered_macros": sorted(covered_public),
            "missing_macros": sorted(missing),
        },
    }


def main() -> int:
    args = _arguments()
    if not 0 <= args.minimum <= 100:
        raise SystemExit("--minimum must be between 0 and 100")
    report = coverage_report(
        args.manifest,
        args.run_results,
        args.public_api,
        args.macros_dir,
    )
    rendered = json.dumps(report, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    public_api = report["public_api"]
    assert isinstance(public_api, dict)
    return (
        0
        if float(report["percent"]) >= args.minimum
        and float(public_api["percent"]) >= args.minimum
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
