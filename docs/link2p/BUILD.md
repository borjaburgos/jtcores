# Link2P build

## Local inputs

The local-only environment file is outside this worktree, in the sibling private
artifact area:

```text
<workspace>/private/link2p.env
```

It contains repository URLs, branch names, artifact root, and placeholders for the external ROM and SD mounts. Do not copy it into Git.

## Supported containers

The repository's current Pocket CI uses `jotego/jtcore20`, not the older Quartus 13.1 path mentioned in the general compilation guide.

Verified locally:

```text
jotego/linter: Verilator 5.050, Icarus Verilog 13.0, Go 1.23.4
jotego/jtcore20: Quartus Prime Lite 20.1.1 Build 720, Go 1.23.4
```

Stock baseline command:

```bash
docker run --rm --network host \
  -v "$PWD:/jtcores" \
  jotego/jtcore20 \
  /jtcores/modules/jtframe/devops/xjtcore.sh bubl pocket
```

The stock ROM-free Pocket output is under `release/pocket/raw`. A ROM is required only to assemble/validate game assets, run ROM-backed simulation, or install a playable package.

## Stable entry points

```bash
make link2p-lint
make link2p-unit
make link2p-link-sim
make link2p-host
make link2p-join
make link2p-diag-host
make link2p-diag-join
make link2p-package ROM=/absolute/path OUT=/absolute/private/path
make link2p-jtbubl-smoke ROM=/absolute/path/to/bublbobl.rom
make link2p-jtbubl-long ROM=/absolute/path/to/bublbobl.rom
```

`link2p-unit` runs five Icarus testbenches in `jotego/linter`. Host and Join
build targets pass mutually exclusive compile-time macros and a common
protocol/build ID to Quartus, try up to four seeds, and preserve the passing
raw package and reports below `PRIVATE_ARTIFACT_ROOT`. Diagnostic builds keep
the status grid visible while the complete JTBUBL instance runs behind it.

The ROM-backed determinism targets require the assembled Bubble Bobble Japan
Ver 0.1 image produced by the current JOTEGO MRA, not the source ZIP. The
accepted image is 786,692 bytes with MD5
`fcbcd7500f6a7421e827373cfa8890d3`, CRC-32 `2d09cf0e`, and SHA-256
`529a46c61e96419cdc307c8bb9116c454eea60ab9a10673ae2be16282be53e80`.
The runner stages it read-only below `PRIVATE_ARTIFACT_ROOT`, extracts the MCU
BRAM slice privately, and never writes ROM-derived content into Git.

The smoke target compares two complete JTBUBL instances for 600 scripted
frames. The long target compares one neutral and two independently scripted
10,000-frame sessions, with isolated writable state and a second common
reset-release timing. The long runner holds both cores in reset for 100 ms
starting only after ROM download; it does not disturb the SDRAM loader. A run
fails on the first video timing, active-pixel, audio-sample, frame-CRC,
short-stream, or frozen-video error. Set `LINK2P_VERILATOR_THREADS` only to
tune host parallelism; two workers are the verified default.

Each running pattern atomically refreshes private previews at
`frames/latest-a.ppm` and `frames/latest-b.ppm` on the first recorded frame and
every 60 frames thereafter. `frames/progress.txt` records the corresponding
simulator frame, paired-frame count, and CRC. On a host with ImageMagick, open
or convert a snapshot with `magick latest-a.ppm latest-a.png`. These derived
screenshots remain under `PRIVATE_ARTIFACT_ROOT` and are not packaged.

The package target refuses a dirty source tree; a ROM, output, or preserved
build path inside the Git worktree; a non-absolute ROM or output path; or a
role/mode mismatch in any preserved build. It hashes the ROM but does not copy
it into the generated bundle. The bundle contains four unique, coexistable
packages: normal Host and Join, plus always-visible diagnostic Host and Join.
If determinism evidence is supplied, packaging accepts only a passing long run
with the same ROM hashes, the neutral pattern and both scripted seeds, a
nonzero alternate reset hold, and at least 10,000 equal, valid, non-frozen A/B
CRCs per pattern.

Install both diagnostic roles on each backed-up card first, so either physical
Pocket can be assigned either role during cable bring-up:

```bash
<bundle>/install-link2p.sh \
  --sd-root /absolute/path/to/sd \
  --role both \
  --mode diagnostic \
  --rom /absolute/path/to/bublbobl.rom \
  --expected-sha256 529a46c61e96419cdc307c8bb9116c454eea60ab9a10673ae2be16282be53e80 \
  --dry-run
```

After the diagnostic transport gate passes, repeat with `--mode normal` for the
playable packages. Remove `--dry-run` only after reviewing every printed
destination, then run the same command without that flag. Existing files are
backed up under `.link2p-backups` on the SD card. No unrelated file is deleted;
the diagnostic, normal Link2P, and stock `jotego.jtbubl` folders have distinct
core and platform IDs. The installer also refuses an SD root that lacks the
normal Pocket `Assets`, `Cores`, and `Platforms` directories.

### Removable-media write access and FAT recovery

Before writing, identify each card by both capacity and filesystem UUID; never
rely on a transient `/dev/sdX` name. Confirm that the mounted UUID is the
intended backed-up 32 GB Pocket card, then run the installer with whatever
explicit removable-drive/write authorization the execution environment
requires. In particular, a protected workspace may present `/run/media` as
read-only even when the host mount is writable. An `EROFS` result from that
workspace boundary does not by itself prove that the card or FAT filesystem is
faulty; retry the reviewed installer with explicit removable-media access.

If a card was disconnected without a clean eject and the host itself mounts it
read-only, unmount it and check the correct partition directly:

```bash
sudo fsck.fat -a -v /dev/sdXN; echo "exit=$?"
```

Repeat the check after any repair (`exit=1`) until a clean pass returns
`exit=0`. Remount it read-write, install, `sync`, compare the installed files'
hashes with the bundle and external ROM, and unmount/eject it before removal.

## Private artifacts

Artifacts are written below the externally configured private root:

```text
<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/<git-short-sha>/
```

Role builds are staged in `JTBUBL-Link2P/work/{normal,diagnostic}/{host,join}`
before final packaging. No generated package intended for sharing contains a
ROM.
