"""Formatting primitives shared by deterministic text emitters."""

from __future__ import annotations

from datetime import date, datetime

import yaml

from ...version import generated_header

GENERATED_HEADER_SQL = generated_header("--")
GENERATED_HEADER_YAML = generated_header("#")


def plain(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def yaml_text(payload: object) -> str:
    return yaml.safe_dump(
        plain(payload),
        sort_keys=False,
        allow_unicode=True,
        width=100,
        default_flow_style=False,
    )


def remove_empty(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: remove_empty(item)
            for key, item in value.items()
            if item is not None and item != [] and item != {}
        }
    if isinstance(value, list):
        return [remove_empty(item) for item in value]
    return value


def jinja(value: object) -> str:
    value = plain(value)
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{jinja(key)}: {jinja(item)}" for key, item in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(jinja(item) for item in value) + "]"
    return str(value)
