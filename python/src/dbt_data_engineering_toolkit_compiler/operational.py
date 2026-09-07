"""Typed operational models shared across brokers, services, and exposers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import JsonValue as JsonValue


@dataclass(frozen=True, slots=True)
class Artifact:
    """A generated text artifact before it is written to an external resource."""

    path: Path
    content: str


@dataclass(frozen=True, slots=True)
class ArtifactChange:
    """A planned change to a generated artifact."""

    action: str
    path: Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Structured result returned by command-line dependency brokers."""

    command: tuple[str, ...]
    return_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0

    @property
    def output(self) -> str:
        return "\n".join(part for part in (self.stdout.strip(), self.stderr.strip()) if part)


@dataclass(frozen=True, slots=True)
class ApplicationResult:
    """Presentation-neutral result returned by an application service."""

    exit_code: int = 0
    messages: tuple[str, ...] = field(default_factory=tuple)
    error_messages: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def success(cls, *messages: str) -> "ApplicationResult":
        return cls(messages=tuple(messages))

    @classmethod
    def failure(cls, *messages: str, exit_code: int = 1) -> "ApplicationResult":
        return cls(exit_code=exit_code, error_messages=tuple(messages))
