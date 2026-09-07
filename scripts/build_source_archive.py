#!/usr/bin/env python3
"""Build and extract-test the portable source release archive."""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

from checks.archive import (
    ARCHIVE_ROOT,
    MAX_ARCHIVE_MEMBER_LENGTH,
    archive_member,
    release_files,
    validate_archive_members,
)
from checks.paths import ROOT


def build_archive(output: Path) -> tuple[int, int]:
    files = release_files()
    members = [archive_member(path) for path in files]
    errors = validate_archive_members(members)
    if errors:
        raise ValueError("\n".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for source, member in zip(files, members, strict=True):
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)

    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"release archive failed CRC validation: {output}")
        if archive.namelist() != members:
            raise ValueError("release archive member list changed during construction")
        with tempfile.TemporaryDirectory(prefix="det-release-extraction-") as temporary:
            archive.extractall(temporary)
            extracted_root = Path(temporary) / ARCHIVE_ROOT
            for source in files:
                extracted = extracted_root / source.relative_to(ROOT)
                if extracted.read_bytes() != source.read_bytes():
                    raise ValueError(
                        f"release extraction changed {source.relative_to(ROOT)}"
                    )

    return len(files), max(map(len, members), default=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / f"{ARCHIVE_ROOT}.zip",
    )
    args = parser.parse_args()
    file_count, longest = build_archive(args.output.resolve())
    print(
        f"Built and extract-tested {args.output} with {file_count} files; "
        f"longest member is {longest}/{MAX_ARCHIVE_MEMBER_LENGTH} characters."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
