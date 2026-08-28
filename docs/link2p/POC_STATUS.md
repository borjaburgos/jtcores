# JTBUBL Link2P POC status

## 2026-08-27 — preflight and stock baseline

### Repositories

```text
Superproject branch: codex/jtbubl-link2p-poc
Superproject base commit: 1268a90e365c2520b412f224ae30d20c61aa0031
Superproject upstream HEAD: 47e6b8dad5b52b6f314813fe3d78807dcce77757
Pocket branch: codex/jtbubl-link2p-poc
Pocket commit/upstream HEAD: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
```

The worktree was created from `borjaburgos/jtcores`; no pre-existing user checkout was modified. `borjaburgos/pocket` is the private development remote. GitHub CLI authentication and permissions are verified.

### Completed work

- Resolved all repository, owner, and base-branch project inputs.
- Created coordinated real branches in the superproject and Pocket submodule.
- Created a local-only environment file and private artifact tree outside the Git worktree.
- Initialized the JTBUBL/JT12/JTOPL dependencies needed by the build.
- Verified the supported official build/test containers.
- Reproduced an unmodified JTBUBL Pocket build and preserved its ROM-free package/reports privately.
- Mapped link pins, controller polarity/order, Start/Coin mapping, reset domains, game LVBL, external Pocket `vblank`, and package generation.
- Selected a target-only Host/Join, two-frame-buffered architecture.

### Commands run

```text
gh auth status
gh repo view ...
git ls-remote ...
docker run --rm jotego/linter ...
docker run --rm jotego/jtcore20 ...
docker run --rm --network host -v <worktree>:/jtcores jotego/jtcore20 /jtcores/modules/jtframe/devops/xjtcore.sh bubl pocket
```

### Passing tests

- Repository access and permissions.
- JTFRAME source generation.
- Quartus analysis, synthesis, fitting, assembly, and timing for stock JTBUBL Pocket.
- Stock RBF copied and SHA-256 verified after preservation.

### Current failures and unavailable inputs

No source/build failure is active.

```text
LOCAL_BUBBLE_BOBBLE_ROM: not supplied
POCKET_A_SD_ROOT: not mounted/supplied
POCKET_B_SD_ROOT: not mounted/supplied
```

Host-native Go, Verilator, Icarus, and Quartus are not installed. This is not blocking because the repository-supported containers are available. A direct `sudo pacman` install was attempted but correctly stopped at the password prompt.

### Decisions

- Use current CI's Quartus 20.1.1 container; the general guide's Quartus 13.1 statement is stale for Pocket.
- Keep JTBUBL unchanged.
- Compile Link2P only for explicit Host/Join macros; stock Pocket remains unchanged.
- Intercept final active-low controls after JTFRAME mapping and before the game instance.
- Use the top-level Pocket `vblank` for linked reset-release arming and game `LVBL` for frame input application.
- Use a fixed two-frame input delay and reset on missing/corrupt required input.

### Hardware status

Not started. No SD card, ROM, Pocket, or cable result has been claimed.

### Next exact command

```bash
make link2p-unit
```

## 2026-08-27 — ROM-free transport, integration, and synthesis

### Repositories

```text
Superproject branch/commit: codex/jtbubl-link2p-poc / b5d437f2d8c7f65079ca69b0eb414ea228ce022c
Pocket branch/commit: codex/jtbubl-link2p-poc / ccb61e5 (three coordinated commits)
Pocket upstream: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
```

### Completed work

- Added the synthesizable 192-bit Host/Join serial endpoint with registered
  CRC-8, gap framing, and explicit Pocket CDC synchronizers.
- Added build/game/DIP/session handshake, VBL-aligned reset release, a
  four-entry frame-keyed buffer, and symmetric N+2 active-low controls.
- Added safe missing-input, CRC, identity, peer, timeout, buffer, and video-CRC
  faults plus quiet fresh-session recovery.
- Added preserved diagnostic signals, active-video CRC-32, and a target status
  grid that remains visible while linked reset is held.
- Added five ROM-free Icarus testbenches and stable Make entry points.
- Added safe role build preservation, ROM-free package transformation, and an
  SD installer with absolute-path validation, dry-run, hashing, backup, and no
  deletion behavior.
- Committed the Pocket work as `c4ab956`, `6b3ba46`, and `ccb61e5`.

### Commands and passing tests

```text
make link2p-unit                         PASS (five testbenches)
make link2p-lint                         PASS (pre-existing Analogizer warnings)
make link2p-host                         PASS seed 0, +0.122 ns checkpoint
make link2p-join                         PASS seed 0, +0.122 ns checkpoint
stock xjtcore.sh bubl pocket             PASS seed 0, +0.109 ns
package-link2p.py with dummy ROM         PASS; no ROM copied
install-link2p.sh --dry-run --role both  PASS; unique stock-safe paths
sha256sum -c SHA256SUMS                  PASS
```

### Current failures and unavailable inputs

No ROM-free test, lint, synthesis, timing, package-layout, or installer dry-run
failure is active.

```text
LOCAL_BUBBLE_BOBBLE_ROM: not supplied
POCKET_A_SD_ROOT: not mounted/supplied
POCKET_B_SD_ROOT: not mounted/supplied
Pocket firmware/physical IDs/cable model: not yet recorded
```

ROM-backed dual-JTBUBL determinism and playable asset installation are blocked
only on the local ROM. Physical transport/gameplay remains blocked on two SD
mounts and the two Pockets.

### Decisions

- A fixed four-slot ring implements the two-frame delay and detects overwrite;
  there is no separate asynchronous FIFO.
- Corrupt packets are rejected and lead to timeout if a required valid packet
  does not arrive. Duplicate/stale packets are flagged and cannot update input.
- Join/Join remains safely waiting because neither endpoint supplies SCK.
- Normal Link2P builds show the status grid only while reset/fault is held;
  diagnostic builds keep it selected for cable bring-up.
- Stock no-Link2P elaboration uses the literal original signal connections and
  keeps every link output disabled. Its RBF hash changes with the embedded Git
  commit and is not expected to equal the base-commit hash.

### Hardware status

Not started. No one-Pocket or two-Pocket success is claimed.

### Next exact command

After the superproject records the Pocket submodule commit:

```bash
source <PRIVATE_ARTIFACT_ROOT>/link2p.env
make link2p-host
make link2p-join
```

These final builds will be tied to the coordinated superproject commit, then
the next required user input is the absolute Bubble Bobble ROM path.

## 2026-08-27 — commit-pinned release-candidate builds

### Repositories and GitHub access

```text
Superproject branch/commit: codex/jtbubl-link2p-poc / 162c6fc41dc5d54ce2174b66153cc80c3b99e3ef
Pocket branch/commit: codex/jtbubl-link2p-poc / ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e
JTCORES upstream master: 47e6b8dad5b52b6f314813fe3d78807dcce77757
Pocket upstream master: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
```

GitHub CLI authentication was reverified as `borjaburgos`: both forks are
admin-accessible, `jotego/jtcores` is readable, and `jotego/pocket` is
writable. The JTCORES fork is public while the Pocket fork and upstream Pocket
repository are private, so no public superproject PR will be opened while it
would expose an inaccessible submodule commit.

### Final ROM-free build results

```text
make link2p-host  PASS seed 0, +0.119 ns, 9,596 ALMs / 9,726 registers
Host RBF SHA-256  e094638f014d0afce836520d70d850cb5fee3b09c25d5106ae2334181a8fec9f

make link2p-join  PASS seed 0, +0.119 ns, 9,586 ALMs / 9,682 registers
Join RBF SHA-256  6382241d35112bf5be01bf21bb4cdc8e5056378ed07b5213a2e93a87fb962b2d
```

Both preserved manifests identify the exact superproject and Pocket commits.
Both use 348,587 memory bits, 70 RAM blocks, 26 DSP blocks, and four PLLs.
Quartus confirms Host drives SCK, Join leaves SCK output disabled, and SI/SO
have the intended directions. Link2P cable pins are covered by the scoped SDC
exceptions rather than appearing in the unconstrained-port lists.

### Current gate and next exact command

The ROM-free implementation, tests, role builds, package transformation, and
safe installer are complete. The first remaining gate is ROM-backed dual-core
determinism. It requires an existing absolute path to the user's legally
obtained Bubble Bobble ROM:

```bash
source <PRIVATE_ARTIFACT_ROOT>/link2p.env
make link2p-jtbubl-smoke ROM=/absolute/path/to/bubble-bobble.rom
```

`LOCAL_BUBBLE_BOBBLE_ROM`, `POCKET_A_SD_ROOT`, and `POCKET_B_SD_ROOT` remain
unset. The ROM is needed now. The SD cards should remain disconnected until
ROM inspection, deterministic dual-instance testing, and final private package
generation have passed.

### Hardware status

Not started. No one-Pocket transport or two-Pocket gameplay success is claimed.

## 2026-08-28 — canonical ROM and dual-JTBUBL smoke gate

### Repositories

```text
Superproject branch/commit: codex/jtbubl-link2p-poc / 9e7f22de9
Pocket branch/commit: codex/jtbubl-link2p-poc / ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e
```

### Completed work

- Identified `Downloads/bublbobl.zip` as Bubble Bobble Japan Ver 0.1: all 18
  member names and CRCs match the public JOTEGO MRA metadata.
- Assembled the ROM only below the private artifact root and matched JOTEGO's
  canonical assembled MD5 `fcbcd7500f6a7421e827373cfa8890d3`.
- Added a simulation-only wrapper containing two complete independent JTBUBL
  instances, synchronous active-video CRC streams, and cycle-level video,
  timing, and audio equality checks.
- Added compact neutral and two-player scripted input schedules, the 600-frame
  smoke target, concurrent isolated 10,000-frame long targets, ROM validation,
  and ROM-free evidence import for final packaging.
- Passed the required 600-frame scripted smoke gate with 601 identical paired
  CRCs and stream SHA-256
  `1d568192333ac80f75f559c92354ee3dc0d793c9f783af20776b4df6593b8a80`.
- Qualified the alternate timing with a 100 ms common post-download reset hold:
  neutral and scripted sessions each produced 63 identical paired frames with
  two distinct CRCs and no SDRAM-loader fault.
- Added atomically refreshed private A/B frame previews and a progress record
  every 60 paired frames so an executing session can be inspected safely.

### Current failures and unavailable inputs

No ROM inspection, assembly, harness, or smoke-test failure is active. The
10,000-frame neutral and scripted determinism gate remains to run.

```text
LOCAL_BUBBLE_BOBBLE_ROM: resolved and verified privately
POCKET_A_SD_ROOT: not mounted/supplied
POCKET_B_SD_ROOT: not mounted/supplied
Pocket firmware/physical IDs/cable model: not yet recorded
```

### Decisions

- Share only the immutable external ROM data pins between simulated instances;
  keep every writable game/MCU/video memory and SDRAM controller independent.
- Use two Verilator workers; a four-worker benchmark produced the same CRC
  stream but was not faster.
- Treat fewer than two distinct CRCs in a 600+ frame run as a frozen-video
  failure, even if A and B match.
- Repeat the scripted pulses beyond MCU release so the long run covers live
  two-player controls. The final schedule waits 720 frames, then repeats P1/P2
  Coin, P2/P1 Start, movement, and actions every 240 frames; private previews
  must visibly confirm gameplay entry.
- Apply alternate reset timing only after ROM transfer; asserting a generic
  absolute-time reset during the download violates the simulated SDRAM command
  sequence.

### Next exact command

```bash
source /home/borjaburgos/Developer/JOTEGO/private/link2p.env
make link2p-jtbubl-long ROM="$LOCAL_BUBBLE_BOBBLE_ROM"
```

### Hardware status

Not started. SD cards should remain disconnected until the 10,000-frame gate
and final private package pass. No physical success is claimed.
