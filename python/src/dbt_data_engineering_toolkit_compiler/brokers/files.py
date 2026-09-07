"""Broker for local filesystem persistence."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Protocol

from ..errors import FileOperationError
from ..operational import JsonValue


class FileBroker(Protocol):
    """Filesystem operations required by compiler services."""

    def exists(self, path: Path) -> bool: ...

    def read_bytes(self, path: Path) -> bytes: ...

    def read_text(self, path: Path) -> str: ...

    def read_json(self, path: Path) -> dict[str, JsonValue]: ...

    def write_text_atomic(self, path: Path, content: str) -> None: ...

    def ensure_directory(self, path: Path) -> None: ...

    def delete(self, path: Path) -> None: ...

    def copy_tree(self, source: Path, destination: Path, ignored: set[str]) -> None: ...


class LocalFileBroker:
    """Production filesystem broker with atomic text writes."""

    def exists(self, path: Path) -> bool:
        return path.exists()

    def read_bytes(self, path: Path) -> bytes:
        try:
            return path.read_bytes()
        except OSError as exc:
            raise FileOperationError(path, f"Could not read {path}: {exc}") from exc

    def read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FileOperationError(path, f"Could not read {path}: {exc}") from exc

    def read_json(self, path: Path) -> dict[str, JsonValue]:
        payload = json.loads(self.read_text(path))
        if not isinstance(payload, dict):
            raise FileOperationError(path, f"Expected {path} to contain a JSON object")
        return payload

    def write_text_atomic(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            os.replace(temporary, path)
        except OSError as exc:
            raise FileOperationError(path, f"Could not write {path}: {exc}") from exc
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def ensure_directory(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise FileOperationError(path, f"Could not create {path}: {exc}") from exc

    def delete(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError as exc:
            raise FileOperationError(path, f"Could not delete {path}: {exc}") from exc

    def copy_tree(self, source: Path, destination: Path, ignored: set[str]) -> None:
        def ignore(_directory: str, names: list[str]) -> set[str]:
            return {name for name in names if name in ignored}

        try:
            shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore)
        except OSError as exc:
            raise FileOperationError(destination, f"Could not copy {source}: {exc}") from exc
