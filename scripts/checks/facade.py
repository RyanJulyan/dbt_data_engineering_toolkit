"""Generated namespace-facade consistency check."""

from __future__ import annotations

from generate_alias_facade import generate


def check_facade() -> list[str]:
    return [f"generated facade is stale: {path}" for path in generate(check=True)]
