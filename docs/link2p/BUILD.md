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
frames. The long target compares neutral and scripted 10,000-frame sessions,
with isolated writable state and a second common reset-release timing. The long
runner holds both cores in reset for 100 ms starting only after ROM download;
it does not disturb the SDRAM loader. A run fails on the first video timing,
active-pixel, audio-sample, frame-CRC, short-stream, or frozen-video error. Set
`LINK2P_VERILATOR_THREADS` only to tune host parallelism; two workers are the
verified default.

Each running pattern atomically refreshes private previews at
`frames/latest-a.ppm` and `frames/latest-b.ppm` on the first recorded frame and
every 60 frames thereafter. `frames/progress.txt` records the corresponding
simulator frame, paired-frame count, and CRC. On a host with ImageMagick, open
or convert a snapshot with `magick latest-a.ppm latest-a.png`. These derived
screenshots remain under `PRIVATE_ARTIFACT_ROOT` and are not packaged.

The package target refuses a non-absolute ROM or output path. It hashes the ROM
but does not copy it into the generated bundle. Install it later with:

```bash
<bundle>/install-link2p.sh \
  --sd-root /absolute/path/to/sd \
  --role both \
  --rom /absolute/path/to/bublbobl.rom \
  --dry-run
```

Remove `--dry-run` only after reviewing every printed destination. Existing
files are backed up under `.link2p-backups` on the SD card. No unrelated file
is deleted and the stock `jotego.jtbubl` folders are never targeted.

## Private artifacts

Artifacts are written below the externally configured private root:

```text
<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/<git-short-sha>/
```

Role builds are staged in `JTBUBL-Link2P/work/normal/{host,join}` before final
packaging. No generated package intended for sharing contains a ROM.
