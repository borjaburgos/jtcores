#!/usr/bin/env python3
"""Create private ROM-free Host/Join Link2P package artifacts."""

from __future__ import annotations

import argparse
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROLE_CONFIG = {
    "host": {
        "core_suffix": "JTBUBLLinkHost",
        "platform": "jtbubl_link2p_host",
        "display": "Bubble Bobble Link2P — Host/P1",
        "rbf": "jtbubl_link2p_host.rbf_r",
    },
    "join": {
        "core_suffix": "JTBUBLLinkJoin",
        "platform": "jtbubl_link2p_join",
        "display": "Bubble Bobble Link2P — Join/P2",
        "rbf": "jtbubl_link2p_join.rbf_r",
    },
}

FORBIDDEN_SUFFIXES = {".rom", ".zip", ".7z", ".sof", ".rbf"}


def run_git(repo: Path, *args: str, fallback: str = "unknown") -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return result.stdout.strip() or fallback
    except (OSError, subprocess.CalledProcessError):
        return fallback


def hashes(path: Path) -> tuple[str, str, int]:
    sha = hashlib.sha256()
    crc = 0
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
            crc = binascii.crc32(chunk, crc)
            size += len(chunk)
    return sha.hexdigest(), f"{crc & 0xFFFFFFFF:08x}", size


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_result(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def copy_determinism_evidence(source: Path, destination: Path) -> dict:
    summary_path = source / "result.txt"
    if not source.is_absolute() or not summary_path.is_file():
        raise RuntimeError("determinism results must be an absolute passing run directory")
    summary = load_result(summary_path)
    if summary.get("result") != "PASS":
        raise RuntimeError(f"determinism run is not passing: {source}")

    destination.mkdir(parents=True)
    shutil.copy2(summary_path, destination / "result.txt")
    patterns = summary.get("patterns", "").split()
    evidence = {"summary": summary, "patterns": {}}
    for pattern in patterns:
        pattern_source = source / pattern
        result_source = pattern_source / "result.txt"
        crc_a = pattern_source / "frames" / "a.crc"
        crc_b = pattern_source / "frames" / "b.crc"
        if not result_source.is_file() or not crc_a.is_file() or not crc_b.is_file():
            raise RuntimeError(f"incomplete determinism evidence for {pattern}: {source}")
        if crc_a.read_bytes() != crc_b.read_bytes():
            raise RuntimeError(f"mismatching determinism CRC streams for {pattern}: {source}")
        pattern_destination = destination / pattern
        pattern_destination.mkdir()
        shutil.copy2(result_source, pattern_destination / "result.txt")
        shutil.copy2(crc_a, pattern_destination / "a.crc")
        shutil.copy2(crc_b, pattern_destination / "b.crc")
        evidence["patterns"][pattern] = {
            "frames": len(crc_a.read_text(encoding="utf-8").splitlines()),
            "crc_stream_sha256": hashes(crc_a)[0],
        }
    return evidence


def validate_source(build_root: Path, role: str) -> tuple[Path, Path]:
    package = build_root / "core-package"
    reports = build_root / "quartus-reports"
    rbf = package / "Cores" / "jotego.jtbubl" / "jtbubl.rbf_r"
    if not rbf.is_file():
        raise RuntimeError(f"{role} build is missing {rbf}")
    for path in package.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES and path != rbf:
            raise RuntimeError(f"{role} source package contains forbidden private/generated file: {path}")
    return package, reports


def source_manifest(build_root: Path, package: Path) -> dict:
    path = build_root / "source-manifest.json"
    if path.is_file():
        return load_json(path)
    core_json = load_json(package / "Cores" / "jotego.jtbubl" / "core.json")
    return {
        "jtcores_commit": core_json["core"]["metadata"].get("version", "unknown"),
        "pocket_commit": "unknown",
    }


def create_role_package(source: Path, destination: Path, role: str, owner: str, version: str, release_date: str) -> Path:
    config = ROLE_CONFIG[role]
    core_id = f"{owner}.{config['core_suffix']}"
    platform = config["platform"]

    core_source = source / "Cores" / "jotego.jtbubl"
    core_destination = destination / "Cores" / core_id
    shutil.copytree(core_source, core_destination)
    old_rbf = core_destination / "jtbubl.rbf_r"
    new_rbf = core_destination / config["rbf"]
    old_rbf.rename(new_rbf)

    core_json_path = core_destination / "core.json"
    core_json = load_json(core_json_path)
    metadata = core_json["core"]["metadata"]
    metadata["platform_ids"] = [platform]
    metadata["shortname"] = f"bubl-link-{role}"
    metadata["description"] = config["display"]
    metadata["author"] = owner
    metadata["url"] = f"https://github.com/{owner}/jtcores"
    metadata["version"] = version
    metadata["date_release"] = release_date
    core_json["core"]["framework"]["hardware"]["link_port"] = True
    core_json["core"]["cores"] = [{
        "name": f"JTBUBL Link2P {role.title()}",
        "id": 0,
        "filename": config["rbf"],
    }]
    write_json(core_json_path, core_json)

    common_destination = destination / "Assets" / platform / "common"
    common_destination.mkdir(parents=True)
    for filename in ("LICENSE", "README"):
        source_file = source / "Assets" / "jtbubl" / "common" / filename
        if source_file.is_file():
            shutil.copy2(source_file, common_destination / filename)

    instance_source = source / "Assets" / "jtbubl" / "jotego.jtbubl" / "Bubble Bobble (Japan, Ver 0.1).json"
    instance_destination = destination / "Assets" / platform / core_id
    instance_destination.mkdir(parents=True)
    shutil.copy2(instance_source, instance_destination / instance_source.name)
    license_source = instance_source.parent / "LICENSE"
    if license_source.is_file():
        shutil.copy2(license_source, instance_destination / "LICENSE")

    platforms = destination / "Platforms"
    (platforms / "_images").mkdir(parents=True)
    platform_json = load_json(source / "Platforms" / "jtbubl.json")
    platform_json["platform"]["name"] = config["display"]
    write_json(platforms / f"{platform}.json", platform_json)
    shutil.copy2(source / "Platforms" / "_images" / "jtbubl.bin", platforms / "_images" / f"{platform}.bin")

    (destination / f"JTBUBL-LINK2P-{role.upper()}.txt").write_text(
        f"{config['display']}\n\n"
        "This is a complete local JTBUBL core. It requires the other Link2P role, "
        "a compatible GB/GBC link cable, and a privately supplied bublbobl.rom.\n"
        "No ROM is included in this package. The stock jotego.jtbubl paths are not changed.\n",
        encoding="utf-8",
    )
    write_json(core_destination / "link2p-build.json", {
        "role": role,
        "protocol_version": 1,
        "build_id": "0x4c325001",
        "input_delay_frames": 2,
        "source_version": version,
        "rom_included": False,
    })
    return new_rbf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--host-build", default=os.environ.get("LINK2P_HOST_BUILD", ""))
    parser.add_argument("--join-build", default=os.environ.get("LINK2P_JOIN_BUILD", ""))
    parser.add_argument("--determinism-results", default=os.environ.get("LINK2P_DETERMINISM_RESULTS", ""))
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "borjaburgos"))
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    pocket_repo = repo / "modules" / "jtframe" / "target" / "pocket"
    rom = Path(args.rom).expanduser()
    output = Path(args.out).expanduser()
    if not rom.is_absolute() or not rom.is_file():
        parser.error("--rom must be an existing absolute file")
    if not output.is_absolute():
        parser.error("--out must be an absolute path")
    output.mkdir(parents=True, exist_ok=True)

    private_root = Path(os.environ.get("PRIVATE_ARTIFACT_ROOT", str(output))).expanduser()
    host_build = Path(args.host_build).expanduser() if args.host_build else private_root / "JTBUBL-Link2P" / "work" / "normal" / "host"
    join_build = Path(args.join_build).expanduser() if args.join_build else private_root / "JTBUBL-Link2P" / "work" / "normal" / "join"
    if not host_build.is_absolute() or not join_build.is_absolute():
        parser.error("Host and Join build roots must be absolute paths")

    host_source, host_reports = validate_source(host_build, "host")
    join_source, join_reports = validate_source(join_build, "join")
    host_source_manifest = source_manifest(host_build, host_source)
    join_source_manifest = source_manifest(join_build, join_source)
    rom_sha, rom_crc, rom_size = hashes(rom)

    super_commit = run_git(repo, "rev-parse", "HEAD")
    pocket_commit = run_git(pocket_repo, "rev-parse", "HEAD")
    dirty = bool(run_git(repo, "status", "--porcelain", fallback="")) or bool(
        run_git(pocket_repo, "status", "--porcelain", fallback="")
    )
    host_version = str(host_source_manifest["jtcores_commit"])[:7]
    join_version = str(join_source_manifest["jtcores_commit"])[:7]
    if host_version != join_version:
        raise RuntimeError(f"Host/Join source versions differ: {host_version} vs {join_version}")
    label = host_version
    final_root = output / "JTBUBL-Link2P" / label
    timestamp = datetime.now(timezone.utc)
    if final_root.exists():
        backup = final_root.with_name(final_root.name + ".backup-" + timestamp.strftime("%Y%m%dT%H%M%SZ"))
        final_root.rename(backup)
        print(f"Preserved prior bundle at {backup}")

    final_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".link2p-package-", dir=final_root.parent) as temp_name:
        temp_root = Path(temp_name)
        host_rbf = create_role_package(host_source, temp_root / "host" / "core-package", "host", args.owner, host_version, timestamp.date().isoformat())
        join_rbf = create_role_package(join_source, temp_root / "join" / "core-package", "join", args.owner, join_version, timestamp.date().isoformat())

        for reports_source, role in ((host_reports, "host"), (join_reports, "join")):
            destination = temp_root / role / "quartus-reports"
            if reports_source.is_dir():
                shutil.copytree(reports_source, destination)
            else:
                destination.mkdir(parents=True)
                (destination / "REPORTS-NOT-PRESERVED.txt").write_text(
                    "Quartus reports were not present beside the supplied role build.\n",
                    encoding="utf-8",
                )

        (temp_root / "simulation" / "unit").mkdir(parents=True)
        (temp_root / "simulation" / "unit" / "RESULT.txt").write_text(
            "Run `make link2p-unit` from the source tree; all five ROM-free testbenches must pass.\n",
            encoding="utf-8",
        )
        determinism = None
        if args.determinism_results:
            determinism = copy_determinism_evidence(
                Path(args.determinism_results).expanduser(),
                temp_root / "simulation" / "determinism",
            )
        else:
            (temp_root / "simulation" / "determinism").mkdir()
        (temp_root / "simulation" / "fault-injection").mkdir()

        shutil.copy2(repo / "scripts" / "link2p" / "install-link2p.sh", temp_root / "install-link2p.sh")
        shutil.copy2(repo / "scripts" / "link2p" / "install-link2p.py", temp_root / "install-link2p.py")
        shutil.copy2(repo / "docs" / "link2p" / "HARDWARE_TEST.md", temp_root / "hardware-test-checklist.md")

        host_sha, _, _ = hashes(host_rbf)
        join_sha, _, _ = hashes(join_rbf)
        submodules = run_git(repo, "submodule", "status", "--recursive").splitlines()
        manifest = {
            "build_timestamp_utc": timestamp.isoformat(),
            "packaging_source_dirty": dirty,
            "jtcores_fork_commit": host_source_manifest["jtcores_commit"],
            "jtcores_upstream_commit": run_git(repo, "rev-parse", "upstream/master"),
            "pocket_target_commit": host_source_manifest["pocket_commit"],
            "pocket_target_upstream_commit": run_git(pocket_repo, "rev-parse", "upstream/master"),
            "packaging_jtcores_commit": super_commit,
            "packaging_pocket_commit": pocket_commit,
            "submodule_commits": submodules,
            "quartus_version": "20.1.1 Build 720",
            "verilator_version": "5.050",
            "protocol_version": 1,
            "build_id": "0x4c325001",
            "host_bitstream_sha256": host_sha,
            "join_bitstream_sha256": join_sha,
            "rom_size": rom_size,
            "rom_crc32": rom_crc,
            "rom_sha256": rom_sha,
            "rom_included": False,
            "dip_configuration": "runtime dipsw[15:0]; peers must match; Bubble Bobble instance write 0x8300",
            "determinism": determinism,
            "known_limitations": [
                "Physical two-Pocket transport and gameplay are not yet verified.",
                *( [] if determinism else ["Dual-JTBUBL long-run determinism requires the private ROM."] ),
                "Join/Join cannot distinguish a missing clock peer from a disconnected cable and remains safely waiting.",
                "Reconnect requires a fresh automatic session and restarts both local game instances.",
            ],
        }
        write_json(temp_root / "build-manifest.json", manifest)

        sum_lines = []
        for path in sorted(temp_root.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                sum_lines.append(f"{hashes(path)[0]}  {path.relative_to(temp_root)}")
        (temp_root / "SHA256SUMS").write_text("\n".join(sum_lines) + "\n", encoding="utf-8")
        temp_root.rename(final_root)

    print(f"Created ROM-free Link2P bundle: {final_root}")
    print(f"ROM size={rom_size} crc32={rom_crc} sha256={rom_sha}")
    print(f"Host bitstream SHA-256: {host_sha}")
    print(f"Join bitstream SHA-256: {join_sha}")
    print("The ROM was hashed but was not copied into the bundle.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"package-link2p: {exc}", file=sys.stderr)
        raise SystemExit(1)
