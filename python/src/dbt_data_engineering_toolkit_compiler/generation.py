"""Drift-safe, deterministic artifact planning and writing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .brokers.files import FileBroker, LocalFileBroker
from .errors import GeneratedFileDriftError
from .operational import Artifact, ArtifactChange, JsonValue
from .version import COMPILER_VERSION

MANIFEST = ".det-manifest.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


Change = ArtifactChange


def load_manifest(root: Path, files: FileBroker) -> dict[str, JsonValue]:
    path = root / MANIFEST
    if not files.exists(path):
        return {"files": {}}
    return files.read_json(path)


def plan_changes(
    root: Path,
    artifacts: list[Artifact],
    *,
    force: bool = False,
    prune: bool = False,
    file_broker: FileBroker | None = None,
) -> tuple[list[Change], dict[str, JsonValue]]:
    files = file_broker or LocalFileBroker()
    old = load_manifest(root, files)
    raw_old_files = old.get("files", {})
    old_files = (
        {str(path): str(checksum) for path, checksum in raw_old_files.items()}
        if isinstance(raw_old_files, dict)
        else {}
    )
    new_files = {artifact.path.as_posix(): sha256_text(artifact.content) for artifact in artifacts}
    changes: list[Change] = []
    drifted: list[str] = []
    for artifact in artifacts:
        relative = artifact.path.as_posix()
        destination = root / artifact.path
        if not files.exists(destination):
            changes.append(Change("create", artifact.path))
            continue
        current_hash = sha256_bytes(files.read_bytes(destination))
        old_hash = old_files.get(relative)
        if old_hash and current_hash != old_hash and not force:
            drifted.append(relative)
        elif current_hash == new_files[relative]:
            changes.append(Change("unchanged", artifact.path))
        else:
            changes.append(Change("update", artifact.path))
    if prune:
        for relative, expected_hash in sorted(old_files.items()):
            if relative in new_files:
                continue
            destination = root / relative
            if files.exists(destination):
                current_hash = sha256_bytes(files.read_bytes(destination))
                if current_hash != expected_hash and not force:
                    drifted.append(relative)
                else:
                    changes.append(Change("delete", Path(relative)))
    if drifted:
        joined = "\n".join(f"  - {item}" for item in drifted)
        raise GeneratedFileDriftError(
            "Refusing to overwrite hand-edited generated files:\n"
            + joined
            + "\nMove the edits into the workbook, or rerun with --force after review."
        )
    manifest_files: dict[str, JsonValue] = dict(new_files)
    if not prune:
        # An omitted managed file is intentionally retained until --prune is
        # requested. Keep it in the manifest so a later prune remains safe and
        # drift-aware instead of silently forgetting ownership.
        manifest_files = {**old_files, **manifest_files}
    manifest: dict[str, JsonValue] = {
        "compiler_version": COMPILER_VERSION,
        "files": manifest_files,
    }
    return changes, manifest


def apply_changes(
    root: Path,
    artifacts: list[Artifact],
    changes: list[Change],
    manifest: dict[str, JsonValue],
    workbook_hash: str,
    *,
    file_broker: FileBroker | None = None,
) -> None:
    files = file_broker or LocalFileBroker()
    by_path = {artifact.path: artifact for artifact in artifacts}
    for change in changes:
        destination = root / change.path
        if change.action in {"create", "update"}:
            files.write_text_atomic(destination, by_path[change.path].content)
        elif change.action == "delete":
            files.delete(destination)
    manifest["workbook_sha256"] = workbook_hash
    files.write_text_atomic(
        root / MANIFEST,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )
