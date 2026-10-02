"""Validate downloaded release data before signing it; never execute its contents."""

import hashlib
import json
from pathlib import Path
import re
import sys


def asset_names(version: str) -> set[str]:
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z][0-9A-Za-z.-]*)?", version):
        raise ValueError("invalid release version")
    return {
        f"obol-selfhost-{version}.tar.gz", f"obol-selfhost-{version}.tar.gz.sha256",
        "release.json", "docker-compose.yml", "install.sh", "obol", "SHA256SUMS",
        f"obol-{version}.tgz", "helm-values.yaml", f"obol-bundle-{version}.tar",
        f"obol-bundle-{version}.tar.sha256",
    }


def validate_metadata(metadata: dict, version: str, release_id: str) -> None:
    expected = asset_names(version) | {"RELEASE_SHA256SUMS"}
    assets = metadata.get("assets", [])
    if (str(metadata.get("id")) != release_id
            or metadata.get("tag_name") != f"selfhost-v{version}"
            or metadata.get("draft") is not True):
        raise ValueError("expected the requested unpublished release")
    names = [a.get("name") for a in assets]
    if len(names) != len(expected) or set(names) != expected:
        raise ValueError("unexpected, duplicate, or missing release assets")
    if any(a.get("state") != "uploaded" or a.get("size", 0) <= 0 for a in assets):
        raise ValueError("incomplete release upload")


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def validate_files(directory: Path, version: str, expected_checksum: str) -> None:
    expected = asset_names(version)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_checksum):
        raise ValueError("invalid checksum identity")
    checksum_file = directory / "RELEASE_SHA256SUMS"
    if digest(checksum_file) != expected_checksum:
        raise ValueError("release checksums changed after dispatch")
    entries = {}
    for line in checksum_file.read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match or match[2] in entries:
            raise ValueError("invalid or duplicate checksum entry")
        entries[match[2]] = match[1]
    if set(entries) != expected:
        raise ValueError("checksums do not cover the exact release assets")
    for name, checksum in entries.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path) != checksum:
            raise ValueError(f"release asset checksum mismatch: {name}")
    manifest = json.loads((directory / "release.json").read_text())
    if (manifest.get("schema_version") != 1 or manifest.get("version") != version
            or not re.fullmatch(r"[0-9a-f]{40}", manifest.get("revision", ""))
            or set(manifest.get("platforms", [])) != {"linux/amd64", "linux/arm64"}):
        raise ValueError("invalid release identity")
    images = manifest.get("images", {})
    if set(images) != {"control", "gateway", "web"}:
        raise ValueError("invalid image set")
    for service, ref in images.items():
        if not isinstance(ref, str) or not re.fullmatch(
            rf"ghcr\.io/tryobol/{service}@sha256:[0-9a-f]{{64}}", ref
        ):
            raise ValueError("image must be an immutable Obol distribution reference")


if __name__ == "__main__":
    try:
        mode, version, identity, path = sys.argv[1:]
        if mode == "metadata":
            validate_metadata(json.loads(Path(path).read_text()), version, identity)
        elif mode == "files":
            validate_files(Path(path), version, identity)
        else:
            raise ValueError("unknown validation mode")
    except (ValueError, KeyError, TypeError, OSError) as error:
        sys.exit(f"Release validation failed: {error}")
