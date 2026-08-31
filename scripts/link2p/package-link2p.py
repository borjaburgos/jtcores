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
import re
import shutil
import subprocess
import sys
import tempfile


ROLE_CONFIG = {
    ("normal", "host"): {
        "core_suffix": "JTBUBLLinkHost",
        "platform": "bubl_l2p_host",
        "display": "Bubble Bobble Link2P Host/P1",
        "rbf": "l2p_h.rbf_r",
        "bitstream_name": "Link2P Host",
    },
    ("normal", "join"): {
        "core_suffix": "JTBUBLLinkJoin",
        "platform": "bubl_l2p_join",
        "display": "Bubble Bobble Link2P Join/P2",
        "rbf": "l2p_j.rbf_r",
        "bitstream_name": "Link2P Join",
    },
    ("diagnostic", "host"): {
        "core_suffix": "JTBUBLLinkDiagHost",
        "platform": "bubl_diag_host",
        "display": "Bubble Bobble L2P Diag Host/P1",
        "rbf": "l2pd_h.rbf_r",
        "bitstream_name": "Link2P Diag H",
    },
    ("diagnostic", "join"): {
        "core_suffix": "JTBUBLLinkDiagJoin",
        "platform": "bubl_diag_join",
        "display": "Bubble Bobble L2P Diag Join/P2",
        "rbf": "l2pd_j.rbf_r",
        "bitstream_name": "Link2P Diag J",
    },
}

FORBIDDEN_SUFFIXES = {".rom", ".zip", ".7z", ".sof", ".rbf", ".rbf_r"}


def validate_role_config(owner: str) -> None:
    if not owner or len(owner) > 31:
        raise RuntimeError("Pocket core author must contain 1-31 characters")
    for (mode, role), config in ROLE_CONFIG.items():
        platform = config["platform"]
        if len(platform) > 15 or re.fullmatch(r"[a-z0-9][a-z0-9_]*", platform) is None:
            raise RuntimeError(f"invalid Pocket platform ID for {mode}/{role}: {platform}")
        if len(config["display"]) > 31:
            raise RuntimeError(f"Pocket platform name is too long for {mode}/{role}")
        if len(config["core_suffix"]) > 31:
            raise RuntimeError(f"Pocket core shortname is too long for {mode}/{role}")
        if len(config["bitstream_name"]) > 15:
            raise RuntimeError(f"Pocket bitstream name is too long for {mode}/{role}")
        if len(config["rbf"]) > 15:
            raise RuntimeError(f"Pocket bitstream filename is too long for {mode}/{role}")


def run_git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        command = " ".join(args)
        raise RuntimeError(f"Git command failed in {repo}: {command}") from exc


def run_git_optional(repo: Path, *args: str) -> str:
    try:
        return run_git(repo, *args) or "unknown"
    except RuntimeError:
        return "unknown"


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


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_result(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def result_integer(result: dict[str, str], key: str, source: Path) -> int:
    try:
        return int(result[key])
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"invalid determinism {key} in {source}") from exc


def load_crc_stream(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or any(not 1 <= len(line) <= 8 for line in lines):
        raise RuntimeError(f"invalid determinism CRC stream: {path}")
    try:
        for line in lines:
            int(line, 16)
    except ValueError as exc:
        raise RuntimeError(f"invalid determinism CRC stream: {path}") from exc
    return lines


def copy_determinism_evidence(
    source: Path,
    destination: Path,
    *,
    rom_size: int,
    rom_crc32: str,
    rom_sha256: str,
) -> dict:
    summary_path = source / "result.txt"
    if not source.is_absolute() or not summary_path.is_file():
        raise RuntimeError("determinism results must be an absolute passing run directory")
    summary = load_result(summary_path)
    if summary.get("result") != "PASS":
        raise RuntimeError(f"determinism run is not passing: {source}")

    requested_frames = result_integer(summary, "requested_frames", source)
    reset_hold_ms = result_integer(summary, "post_download_reset_hold_ms", source)
    patterns = summary.get("patterns", "").split()
    if summary.get("mode") != "long" or requested_frames < 10_000:
        raise RuntimeError(f"determinism evidence is not a 10,000-frame long run: {source}")
    if patterns != ["neutral", "scripted", "scripted_alt"]:
        raise RuntimeError(
            f"determinism evidence must contain neutral and both scripted seeds: {source}"
        )
    if reset_hold_ms <= 0:
        raise RuntimeError(f"determinism evidence is missing the alternate reset timing: {source}")
    expected_rom = {
        "rom_size": str(rom_size),
        "rom_crc32": rom_crc32,
        "rom_sha256": rom_sha256,
    }
    if any(summary.get(key) != value for key, value in expected_rom.items()):
        raise RuntimeError(f"determinism evidence ROM does not match the packaged ROM: {source}")

    destination.mkdir(parents=True)
    shutil.copy2(summary_path, destination / "result.txt")
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
        crc_lines = load_crc_stream(crc_a)
        if len(crc_lines) < requested_frames:
            raise RuntimeError(
                f"short determinism CRC stream for {pattern}: "
                f"{len(crc_lines)} < {requested_frames}"
            )
        if len(set(crc_lines)) < 2:
            raise RuntimeError(f"frozen determinism CRC stream for {pattern}: {source}")
        if not result_source.read_text(encoding="utf-8").rstrip().endswith("PASS"):
            raise RuntimeError(f"pattern result is not passing for {pattern}: {source}")
        pattern_destination = destination / pattern
        pattern_destination.mkdir()
        shutil.copy2(result_source, pattern_destination / "result.txt")
        shutil.copy2(crc_a, pattern_destination / "a.crc")
        shutil.copy2(crc_b, pattern_destination / "b.crc")
        evidence["patterns"][pattern] = {
            "frames": len(crc_lines),
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


def source_manifest(build_root: Path) -> dict:
    path = build_root / "source-manifest.json"
    if not path.is_file():
        raise RuntimeError(f"build is missing its source manifest: {build_root}")
    return load_json(path)


def validate_source_manifest(manifest: dict, build_root: Path, role: str, mode: str) -> None:
    if manifest.get("role") != role or manifest.get("mode") != mode:
        raise RuntimeError(
            f"build manifest role/mode mismatch in {build_root}: "
            f"expected {role}/{mode}"
        )
    for key in ("jtcores_commit", "pocket_commit"):
        value = manifest.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise RuntimeError(f"invalid {key} in {build_root}")
    seed = manifest.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise RuntimeError(f"invalid Quartus seed in {build_root}")


def validate_matching_sources(named_manifests: tuple[tuple[str, dict], ...]) -> None:
    reference_name, reference = named_manifests[0]
    for name, manifest in named_manifests[1:]:
        for key in ("jtcores_commit", "pocket_commit"):
            if manifest[key] != reference[key]:
                raise RuntimeError(
                    f"{name} and {reference_name} {key} values differ: "
                    f"{manifest[key]} vs {reference[key]}"
                )


def create_role_package(
    source: Path,
    destination: Path,
    role: str,
    mode: str,
    owner: str,
    version: str,
    release_date: str,
) -> Path:
    config = ROLE_CONFIG[(mode, role)]
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
    metadata["shortname"] = config["core_suffix"]
    metadata["description"] = config["display"]
    metadata["author"] = owner
    metadata["url"] = f"https://github.com/{owner}/jtcores"
    metadata["version"] = version
    metadata["date_release"] = release_date
    core_json["core"]["framework"]["hardware"]["link_port"] = True
    core_json["core"]["cores"] = [{
        "name": config["bitstream_name"],
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

    (destination / f"JTBUBL-LINK2P-{mode.upper()}-{role.upper()}.txt").write_text(
        f"{config['display']}\n\n"
        "This is a complete local JTBUBL core. It requires the other Link2P role, "
        "a compatible GB/GBC link cable, and a privately supplied bublbobl.rom.\n"
        + (
            "This diagnostic build keeps the transport status grid visible for cable bring-up.\n"
            if mode == "diagnostic" else ""
        )
        + "No ROM is included in this package. The stock jotego.jtbubl paths are not changed.\n",
        encoding="utf-8",
    )
    write_json(core_destination / "link2p-build.json", {
        "role": role,
        "mode": mode,
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
    parser.add_argument("--diagnostic-host-build", default=os.environ.get("LINK2P_DIAG_HOST_BUILD", ""))
    parser.add_argument("--diagnostic-join-build", default=os.environ.get("LINK2P_DIAG_JOIN_BUILD", ""))
    parser.add_argument("--determinism-results", default=os.environ.get("LINK2P_DETERMINISM_RESULTS", ""))
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "borjaburgos"))
    args = parser.parse_args()
    validate_role_config(args.owner)

    repo = Path(__file__).resolve().parents[2]
    pocket_repo = repo / "modules" / "jtframe" / "target" / "pocket"
    rom = Path(args.rom).expanduser()
    output = Path(args.out).expanduser()
    if not rom.is_absolute() or not rom.is_file():
        parser.error("--rom must be an existing absolute file")
    if not output.is_absolute():
        parser.error("--out must be an absolute path")
    rom = rom.resolve()
    output = output.resolve(strict=False)
    if is_within(rom, repo):
        parser.error("--rom must remain outside the Git worktree")
    if is_within(output, repo):
        parser.error("--out must remain outside the Git worktree")
    output.mkdir(parents=True, exist_ok=True)

    private_root = Path(os.environ.get("PRIVATE_ARTIFACT_ROOT", str(output))).expanduser()
    host_build = Path(args.host_build).expanduser() if args.host_build else private_root / "JTBUBL-Link2P" / "work" / "normal" / "host"
    join_build = Path(args.join_build).expanduser() if args.join_build else private_root / "JTBUBL-Link2P" / "work" / "normal" / "join"
    diagnostic_host_build = (
        Path(args.diagnostic_host_build).expanduser()
        if args.diagnostic_host_build
        else private_root / "JTBUBL-Link2P" / "work" / "diagnostic" / "host"
    )
    diagnostic_join_build = (
        Path(args.diagnostic_join_build).expanduser()
        if args.diagnostic_join_build
        else private_root / "JTBUBL-Link2P" / "work" / "diagnostic" / "join"
    )
    build_roots = (host_build, join_build, diagnostic_host_build, diagnostic_join_build)
    if any(not build_root.is_absolute() for build_root in build_roots):
        parser.error("Normal and diagnostic Host/Join build roots must be absolute paths")
    build_roots = tuple(build_root.resolve() for build_root in build_roots)
    if any(is_within(build_root, repo) for build_root in build_roots):
        parser.error("Normal and diagnostic build roots must remain outside the Git worktree")
    host_build, join_build, diagnostic_host_build, diagnostic_join_build = build_roots

    host_source, host_reports = validate_source(host_build, "host")
    join_source, join_reports = validate_source(join_build, "join")
    diagnostic_host_source, diagnostic_host_reports = validate_source(
        diagnostic_host_build, "diagnostic host"
    )
    diagnostic_join_source, diagnostic_join_reports = validate_source(
        diagnostic_join_build, "diagnostic join"
    )
    host_source_manifest = source_manifest(host_build)
    join_source_manifest = source_manifest(join_build)
    diagnostic_host_manifest = source_manifest(diagnostic_host_build)
    diagnostic_join_manifest = source_manifest(diagnostic_join_build)
    validate_source_manifest(host_source_manifest, host_build, "host", "normal")
    validate_source_manifest(join_source_manifest, join_build, "join", "normal")
    validate_source_manifest(
        diagnostic_host_manifest, diagnostic_host_build, "host", "diagnostic"
    )
    validate_source_manifest(
        diagnostic_join_manifest, diagnostic_join_build, "join", "diagnostic"
    )
    named_manifests = (
        ("normal Host", host_source_manifest),
        ("normal Join", join_source_manifest),
        ("diagnostic Host", diagnostic_host_manifest),
        ("diagnostic Join", diagnostic_join_manifest),
    )
    validate_matching_sources(named_manifests)
    rom_sha, rom_crc, rom_size = hashes(rom)

    super_commit = run_git(repo, "rev-parse", "HEAD")
    pocket_commit = run_git(pocket_repo, "rev-parse", "HEAD")
    dirty = bool(run_git(repo, "status", "--porcelain")) or bool(
        run_git(pocket_repo, "status", "--porcelain")
    )
    if dirty:
        raise RuntimeError("refusing to package from a dirty superproject or Pocket worktree")
    host_version = str(host_source_manifest["jtcores_commit"])[:7]
    join_version = str(join_source_manifest["jtcores_commit"])[:7]
    diagnostic_host_version = str(diagnostic_host_manifest["jtcores_commit"])[:7]
    diagnostic_join_version = str(diagnostic_join_manifest["jtcores_commit"])[:7]
    if host_version != join_version:
        raise RuntimeError(f"Host/Join source versions differ: {host_version} vs {join_version}")
    if diagnostic_host_version != diagnostic_join_version:
        raise RuntimeError(
            "Diagnostic Host/Join source versions differ: "
            f"{diagnostic_host_version} vs {diagnostic_join_version}"
        )
    # Name the bundle after the bitstream source. Packaging may legitimately
    # run from a later clean documentation/tooling commit, which is recorded
    # separately in build-manifest.json.
    label = host_version
    final_root = output / "JTBUBL-Link2P" / label
    timestamp = datetime.now(timezone.utc)

    final_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".link2p-package-", dir=final_root.parent) as temp_name:
        temp_root = Path(temp_name)
        release_date = timestamp.date().isoformat()
        host_rbf = create_role_package(
            host_source, temp_root / "host" / "core-package",
            "host", "normal", args.owner, host_version, release_date,
        )
        join_rbf = create_role_package(
            join_source, temp_root / "join" / "core-package",
            "join", "normal", args.owner, join_version, release_date,
        )
        diagnostic_host_rbf = create_role_package(
            diagnostic_host_source, temp_root / "diagnostic" / "host" / "core-package",
            "host", "diagnostic", args.owner, diagnostic_host_version, release_date,
        )
        diagnostic_join_rbf = create_role_package(
            diagnostic_join_source, temp_root / "diagnostic" / "join" / "core-package",
            "join", "diagnostic", args.owner, diagnostic_join_version, release_date,
        )

        report_sets = (
            (host_reports, Path("host")),
            (join_reports, Path("join")),
            (diagnostic_host_reports, Path("diagnostic/host")),
            (diagnostic_join_reports, Path("diagnostic/join")),
        )
        for reports_source, relative in report_sets:
            destination = temp_root / relative / "quartus-reports"
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
            "Run `make link2p-unit` from the source tree; all six ROM-free testbenches must pass.\n",
            encoding="utf-8",
        )
        determinism = None
        if args.determinism_results:
            determinism = copy_determinism_evidence(
                Path(args.determinism_results).expanduser(),
                temp_root / "simulation" / "determinism",
                rom_size=rom_size,
                rom_crc32=rom_crc,
                rom_sha256=rom_sha,
            )
        else:
            (temp_root / "simulation" / "determinism").mkdir()
        (temp_root / "simulation" / "fault-injection").mkdir()

        shutil.copy2(repo / "scripts" / "link2p" / "install-link2p.sh", temp_root / "install-link2p.sh")
        shutil.copy2(repo / "scripts" / "link2p" / "install-link2p.py", temp_root / "install-link2p.py")
        shutil.copy2(repo / "docs" / "link2p" / "HARDWARE_TEST.md", temp_root / "hardware-test-checklist.md")

        host_sha, _, _ = hashes(host_rbf)
        join_sha, _, _ = hashes(join_rbf)
        diagnostic_host_sha, _, _ = hashes(diagnostic_host_rbf)
        diagnostic_join_sha, _, _ = hashes(diagnostic_join_rbf)
        submodules = run_git(repo, "submodule", "status", "--recursive").splitlines()
        manifest = {
            "build_timestamp_utc": timestamp.isoformat(),
            "packaging_source_dirty": dirty,
            "jtcores_fork_commit": host_source_manifest["jtcores_commit"],
            "jtcores_upstream_commit": run_git_optional(repo, "rev-parse", "upstream/master"),
            "pocket_target_commit": host_source_manifest["pocket_commit"],
            "pocket_target_upstream_commit": run_git_optional(
                pocket_repo, "rev-parse", "upstream/master"
            ),
            "packaging_jtcores_commit": super_commit,
            "packaging_pocket_commit": pocket_commit,
            "submodule_commits": submodules,
            "quartus_version": "20.1.1 Build 720",
            "verilator_version": "5.050",
            "protocol_version": 1,
            "build_id": "0x4c325001",
            "host_bitstream_sha256": host_sha,
            "join_bitstream_sha256": join_sha,
            "diagnostic_jtcores_fork_commit": diagnostic_host_manifest["jtcores_commit"],
            "diagnostic_pocket_target_commit": diagnostic_host_manifest["pocket_commit"],
            "diagnostic_host_bitstream_sha256": diagnostic_host_sha,
            "diagnostic_join_bitstream_sha256": diagnostic_join_sha,
            "rom_size": rom_size,
            "rom_crc32": rom_crc,
            "rom_sha256": rom_sha,
            "rom_included": False,
            "dip_configuration": "runtime dipsw[15:0]; peers must match; Bubble Bobble instance write 0x8300",
            "determinism": determinism,
            "known_limitations": [
                "Cable loss resets both local games; interrupted gameplay and progress are intentionally discarded.",
                *( [] if determinism else ["Dual-JTBUBL long-run determinism requires the private ROM."] ),
                "Join/Join cannot distinguish a missing clock peer from a disconnected cable and remains safely waiting.",
                "Reconnect creates a fresh automatic session and clean game restart; live-game state is not preserved or resumed.",
            ],
        }
        write_json(temp_root / "build-manifest.json", manifest)

        sum_lines = []
        for path in sorted(temp_root.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                sum_lines.append(f"{hashes(path)[0]}  {path.relative_to(temp_root)}")
        (temp_root / "SHA256SUMS").write_text("\n".join(sum_lines) + "\n", encoding="utf-8")
        if final_root.exists():
            backup = final_root.with_name(
                final_root.name + ".backup-" + timestamp.strftime("%Y%m%dT%H%M%SZ")
            )
            final_root.rename(backup)
            print(f"Preserved prior bundle at {backup}")
        temp_root.rename(final_root)

    print(f"Created ROM-free Link2P bundle: {final_root}")
    print(f"ROM size={rom_size} crc32={rom_crc} sha256={rom_sha}")
    print(f"Host bitstream SHA-256: {host_sha}")
    print(f"Join bitstream SHA-256: {join_sha}")
    print(f"Diagnostic Host bitstream SHA-256: {diagnostic_host_sha}")
    print(f"Diagnostic Join bitstream SHA-256: {diagnostic_join_sha}")
    print("The ROM was hashed but was not copied into the bundle.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"package-link2p: {exc}", file=sys.stderr)
        raise SystemExit(1)
