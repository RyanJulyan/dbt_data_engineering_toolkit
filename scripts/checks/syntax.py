"""YAML and Jinja syntax checks."""

from __future__ import annotations

import re

import yaml
from jinja2 import Environment, TemplateSyntaxError

from .paths import ALIAS_ROOT, ROOT

IGNORED_DIRECTORIES = {"target", "dbt_packages", ".venv", "venv"}


def check_yaml() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.yml")):
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
    return errors


def check_jinja() -> list[str]:
    errors: list[str] = []
    environment = Environment(extensions=["jinja2.ext.do"])
    paths = sorted((ROOT / "dbt" / "macros").rglob("*.sql"))
    paths += sorted((ALIAS_ROOT / "macros").rglob("*.sql"))
    for path in paths:
        source = path.read_text(encoding="utf-8")
        parse_source = re.sub(r"({%-?\s*)test(\s+)", r"\1macro\2", source)
        parse_source = re.sub(
            r"({%-?\s*)endtest(\s*-?%})", r"\1endmacro\2", parse_source
        )
        try:
            environment.parse(parse_source)
        except TemplateSyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid Jinja: {exc}")
    return errors
