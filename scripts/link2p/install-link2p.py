#!/usr/bin/env python3
"""Safely install private Link2P packages and an external ROM onto Pocket SD."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone


ROLE_DATA = {
    ("normal", "host"): ("JTBUBLLinkHost", "bubl_l2p_host"),
    ("normal", "join"): ("JTBUBLLinkJoin", "bubl_l2p_join"),
    ("diagnostic", "host"): (
        "JTBUBLLinkDiagHost", "bubl_diag_host"
    ),
    ("diagnostic", "join"): (
        "JTBUBLLinkDiagJoin", "bubl_diag_join"
    ),
}

LEGACY_PLATFORM_IDS = {
    ("normal", "host"): "jtbubl_link2p_host",
    ("normal", "join"): "jtbubl_link2p_join",
    ("diagnostic", "host"): "jtbubl_link2p_diag_host",
    ("diagnostic", "join"): "jtbubl_link2p_diag_join",
}


def file_hashes(path: Path) -> tuple[str, str, int]:
    sha256 = hashlib.sha256()
    crc = 0
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha256.update(chunk)
            crc = binascii.crc32(chunk, crc)
            size += len(chunk)
    return sha256.hexdigest(), f"{crc & 0xFFFFFFFF:08x}", size


def same_file(source: Path, destination: Path) -> bool:
    if not destination.is_file() or source.stat().st_size != destination.stat().st_size:
        return False
    return file_hashes(source)[0] == file_hashes(destination)[0]


def copy_one(source: Path, destination: Path, sd_root: Path, backup_root: Path, dry_run: bool) -> None:
    destination = destination.resolve(strict=False)
    try:
        relative = destination.relative_to(sd_root)
    except ValueError as exc:
        raise RuntimeError(f"refusing destination outside SD root: {destination}") from exc

    if same_file(source, destination):
        print(f"UNCHANGED {relative}")
        return

    if destination.exists():
        backup = backup_root / relative
        print(f"BACKUP {relative} -> {backup.relative_to(sd_root)}")
        if not dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)

    print(f"COPY {source} -> {relative}")
    if dry_run:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".link2p-", dir=destination.parent, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)


def package_files(package_root: Path):
    for source in sorted(package_root.rglob("*")):
        if source.is_symlink():
            raise RuntimeError(f"package contains a symlink: {source}")
        if source.is_file():
            yield source, source.relative_to(package_root)


def retire_legacy_platform(
    platform_id: str, sd_root: Path, backup_root: Path, dry_run: bool
) -> None:
    relative_paths = (
        Path("Assets") / platform_id,
        Path("Platforms") / f"{platform_id}.json",
        Path("Platforms") / "_images" / f"{platform_id}.bin",
    )
    for relative in relative_paths:
        source = sd_root / relative
        if not source.exists():
            continue
        destination = backup_root / "retired-platforms" / relative
        print(f"RETIRE {relative} -> {destination.relative_to(sd_root)}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sd-root", required=True)
    parser.add_argument("--role", required=True, choices=("host", "join", "both"))
    parser.add_argument("--mode", choices=("normal", "diagnostic"), default="normal")
    parser.add_argument("--rom", required=True)
    parser.add_argument("--bundle-root")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sd_root = Path(args.sd_root).expanduser()
    rom = Path(args.rom).expanduser()
    if not sd_root.is_absolute() or not sd_root.is_dir():
        parser.error("--sd-root must be an existing absolute directory")
    if not rom.is_absolute() or not rom.is_file():
        parser.error("--rom must be an existing absolute file")
    sd_root = sd_root.resolve()
    rom = rom.resolve()
    missing_sd_folders = [
        folder for folder in ("Assets", "Cores", "Platforms")
        if not (sd_root / folder).is_dir()
    ]
    if missing_sd_folders:
        parser.error(
            "--sd-root does not look like a prepared Pocket card; missing: "
            + ", ".join(missing_sd_folders)
        )

    bundle_root = Path(args.bundle_root).expanduser() if args.bundle_root else Path(__file__).resolve().parent
    if not bundle_root.is_absolute() or not bundle_root.is_dir():
        parser.error("--bundle-root must be an existing absolute directory")
    bundle_root = bundle_root.resolve()

    rom_sha256, rom_crc32, rom_size = file_hashes(rom)
    expected = args.expected_sha256 or os.environ.get("LINK2P_EXPECTED_ROM_SHA256", "")
    if expected and rom_sha256.lower() != expected.lower():
        parser.error(f"ROM SHA-256 mismatch: expected {expected}, got {rom_sha256}")

    print(f"ROM {rom}")
    print(f"ROM size={rom_size} crc32={rom_crc32} sha256={rom_sha256}")
    print(f"SD root {sd_root}")
    print(f"Package mode {args.mode}")
    if args.dry_run:
        print("DRY RUN: no files will be changed")

    roles = ("host", "join") if args.role == "both" else (args.role,)
    package_base = bundle_root if args.mode == "normal" else bundle_root / "diagnostic"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = sd_root / ".link2p-backups" / timestamp

    for role in roles:
        package_root = package_base / role / "core-package"
        if not package_root.is_dir():
            parser.error(f"missing {role} package: {package_root}")

        configured_core_suffix, platform_id = ROLE_DATA[(args.mode, role)]
        core_matches = list((package_root / "Cores").glob("*.JTBUBLLink*"))
        if len(core_matches) != 1:
            parser.error(f"{role} package has no unique Link2P core folder")
        actual_core_id = core_matches[0].name
        if actual_core_id.split(".", 1)[-1] != configured_core_suffix:
            parser.error(f"unexpected {role} core identifier: {actual_core_id}")

        for source, relative in package_files(package_root):
            if source.suffix.lower() in {".rom", ".zip", ".7z"}:
                parser.error(f"package unexpectedly contains private content: {source}")
            copy_one(source, sd_root / relative, sd_root, backup_root, args.dry_run)

        rom_destination = sd_root / "Assets" / platform_id / "common" / "bublbobl.rom"
        copy_one(rom, rom_destination, sd_root, backup_root, args.dry_run)

        hash_text = (
            f"source={rom}\nsize={rom_size}\ncrc32={rom_crc32}\n"
            f"sha256={rom_sha256}\ninstalled_utc={timestamp}\n"
        )
        hash_destination = rom_destination.with_name("link2p-rom-hashes.txt")
        hash_relative = hash_destination.relative_to(sd_root)
        if hash_destination.exists():
            hash_backup = backup_root / hash_relative
            print(f"BACKUP {hash_relative} -> {hash_backup.relative_to(sd_root)}")
            if not args.dry_run:
                hash_backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hash_destination, hash_backup)
        print(f"WRITE {hash_destination.relative_to(sd_root)}")
        if not args.dry_run:
            hash_destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", prefix=".link2p-hash-",
                dir=hash_destination.parent, delete=False
            ) as temp:
                temp.write(hash_text)
                temp_path = Path(temp.name)
            os.replace(temp_path, hash_destination)

        retire_legacy_platform(
            LEGACY_PLATFORM_IDS[(args.mode, role)],
            sd_root,
            backup_root,
            args.dry_run,
        )

    print("Install plan complete" if args.dry_run else "Install complete")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"install-link2p: {exc}", file=sys.stderr)
        raise SystemExit(1)
