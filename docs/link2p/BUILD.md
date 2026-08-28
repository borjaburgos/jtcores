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

## Planned stable entry points

```bash
make link2p-lint
make link2p-unit
make link2p-link-sim
make link2p-host
make link2p-join
make link2p-package ROM=/absolute/path OUT=/absolute/private/path
```

Host and Join build targets pass mutually exclusive compile-time macros and a common protocol/build ID. The package target refuses a non-absolute ROM or output path.

## Private artifacts

Artifacts are written below the externally configured private root:

```text
<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/<git-short-sha>/
```

No generated package intended for sharing contains a ROM.
