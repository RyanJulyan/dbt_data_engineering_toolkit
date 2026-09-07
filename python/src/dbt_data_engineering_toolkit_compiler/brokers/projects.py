"""Transactional local project workspace operations."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Protocol

from ..errors import FileOperationError

TRANSIENT_PROJECT_DIRECTORIES = frozenset(
    {
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "dbt_packages",
        "logs",
        "target",
    }
)


def _ignore_transient_project_paths(_directory: str, names: list[str]) -> set[str]:
    """Exclude reproducible runtime state from a generated-project transaction."""

    return set(TRANSIENT_PROJECT_DIRECTORIES.intersection(names))


class ProjectWorkspaceBroker(Protocol):
    """Stage and publish a complete generated project as one unit."""

    def stage(self, destination: Path) -> Path: ...

    def publish(self, staging: Path, destination: Path) -> None: ...

    def cleanup(self, staging: Path) -> None: ...

    def delete_tree(self, path: Path) -> None: ...

    def copy_file(self, source: Path, destination: Path) -> None: ...

    def list_files(self, root: Path) -> list[Path]: ...


class LocalProjectWorkspaceBroker:
    """Sibling-directory staging with rollback-safe publication."""

    def stage(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            staging = Path(
                tempfile.mkdtemp(
                    prefix=f".{destination.name}.det-stage-",
                    dir=destination.parent,
                )
            )
            if destination.exists():
                shutil.copytree(
                    destination,
                    staging,
                    dirs_exist_ok=True,
                    ignore=_ignore_transient_project_paths,
                )
            return staging
        except OSError as exc:
            raise FileOperationError(
                destination,
                f"Could not stage generated project {destination}: {exc}",
            ) from exc

    def publish(self, staging: Path, destination: Path) -> None:
        backup = destination.parent / f".{destination.name}.det-backup-{uuid.uuid4().hex}"
        moved_existing = False
        try:
            if destination.exists():
                os.replace(destination, backup)
                moved_existing = True
            os.replace(staging, destination)
        except OSError as exc:
            if moved_existing and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise FileOperationError(
                destination,
                f"Could not publish generated project {destination}: {exc}",
            ) from exc
        else:
            if backup.exists():
                shutil.rmtree(backup)

    def cleanup(self, staging: Path) -> None:
        try:
            if staging.exists():
                shutil.rmtree(staging)
        except OSError as exc:
            raise FileOperationError(staging, f"Could not clean staging project: {exc}") from exc

    def delete_tree(self, path: Path) -> None:
        try:
            if path.exists():
                shutil.rmtree(path)
        except OSError as exc:
            raise FileOperationError(
                path, f"Could not remove generated tree {path}: {exc}"
            ) from exc

    def copy_file(self, source: Path, destination: Path) -> None:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        except OSError as exc:
            raise FileOperationError(
                destination,
                f"Could not preserve managed file {source}: {exc}",
            ) from exc

    def list_files(self, root: Path) -> list[Path]:
        if not root.exists():
            return []
        try:
            return sorted(path for path in root.rglob("*") if path.is_file())
        except OSError as exc:
            raise FileOperationError(
                root, f"Could not inspect generated tree {root}: {exc}"
            ) from exc
