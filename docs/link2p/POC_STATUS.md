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
- Added compact neutral and two independent two-player scripted schedules, the
  600-frame smoke target, concurrent isolated 10,000-frame long targets, ROM
  validation, and ROM-free evidence import for final packaging.
- Passed the required 600-frame scripted smoke gate with 601 identical paired
  CRCs and stream SHA-256
  `1d568192333ac80f75f559c92354ee3dc0d793c9f783af20776b4df6593b8a80`.
- Qualified the alternate timing with a 100 ms common post-download reset hold:
  neutral and scripted sessions each produced 63 identical paired frames with
  two distinct CRCs and no SDRAM-loader fault.
- Added atomically refreshed private A/B frame previews and a progress record
  every 60 paired frames so an executing session can be inspected safely.
- Hardened final evidence import so a short qualification, wrong ROM, missing
  input pattern, default reset timing, malformed/mismatched CRC stream, or
  frozen output cannot satisfy the 10,000-frame packaging gate.

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
  two-player controls. Both final seeds wait 720 frames, then repeat P1/P2 Coin,
  both Start buttons, movement, and actions every 240 frames with different
  phases; private previews must visibly confirm gameplay entry.
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

## 2026-08-28 — diagnostic builds and executing long gate

### Repositories

```text
Superproject branch/model commit: codex/jtbubl-link2p-poc / 8f48f41158aa45eddee17e2ad28d06e72858d679
Pocket branch/commit: codex/jtbubl-link2p-poc / ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e
JTCORES upstream master: 47e6b8dad5b52b6f314813fe3d78807dcce77757
Pocket upstream master: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
```

Packaging/installer documentation changes remain intentionally uncommitted
while the long simulator is executing. Its final manifest reads `HEAD`, so the
compiled model and recorded commit must remain `8f48f4115` until it exits.

### Completed work and passing tests

- Diagnostic Host: Quartus PASS seed 0, +0.090 ns, 9,573 ALMs / 9,670
  registers, RBF SHA-256
  `9a423870c5f9728c957f4a909b6da9cbc0c166398eafe9357938c2d723ebb0ce`.
- Diagnostic Join: Quartus PASS seed 0, +0.096 ns, 9,584 ALMs / 9,628
  registers, RBF SHA-256
  `acee8ddb27d5d963cdc24dba0bfc9cae1035a9b44dfea470ec85b779e0325d98`.
- Added four coexistable package identities: normal Host/Join and diagnostic
  Host/Join. Component packaging, `SHA256SUMS`, ROM exclusion, prepared-SD
  validation, and normal/diagnostic installer dry-runs pass against temporary
  two-card layouts while preserving a stock-core marker.
- GitHub CLI authentication works as `borjaburgos`; the Pocket draft PR is
  open and its description now records the smoke, synthesis, privacy, and
  current long-run status.
- The live long run has three isolated patterns (`neutral`, `scripted`, and
  `scripted_alt`), each containing two complete JTBUBL instances. At recorded
  frame 1,440, all three full A/B CRC streams remain identical.
- Scripted cabinet input logs confirm repeated P1/P2 Select/Coin transitions.
  The paired frame-1,440 preview visibly shows Round 1 with both players,
  enemies, and bubbles, and the A/B PPM SHA-256 values are identical.

### Current failures and unavailable inputs

No simulation mismatch or packaging-component failure is active. The long run
has not yet reached its required 10,000 paired frames per pattern, so no
long-run PASS or final private bundle is claimed.

```text
LOCAL_BUBBLE_BOBBLE_ROM: resolved and verified privately
POCKET_A_SD_ROOT: not mounted/supplied
POCKET_B_SD_ROOT: not mounted/supplied
Pocket A/B firmware and physical IDs: not yet recorded
SD-card identifiers: not yet recorded
Cable type/model: not yet recorded
```

### Next exact command

After the three existing named containers finish, inspect their generated
`result.txt`, commit the packaging/ledger milestone, and package the clean tree
with the passing run:

```bash
source /home/borjaburgos/Developer/JOTEGO/private/link2p.env
export LINK2P_DETERMINISM_RESULTS=/home/borjaburgos/Developer/JOTEGO/private/JTBUBL-Link2P/simulation/determinism/long-8f48f41158aa-VGrO0G
make link2p-package ROM="$LOCAL_BUBBLE_BOBBLE_ROM" OUT="$PRIVATE_ARTIFACT_ROOT"
```

### Hardware status

Not started. Keep both SD cards disconnected until the long gate, clean final
package, checksum verification, and two temporary-card installs pass. No
physical transport or gameplay success is claimed.

## 2026-08-28 — completed long determinism gate

### Passing result

The neutral, primary scripted, and alternate scripted sessions each reached
the requested terminal window with 10,061 paired active-frame CRCs. In every
session the full A and B streams are byte-identical, the final frame images are
byte-identical, and the output is non-frozen:

```text
neutral       10,061 frames  5,008 distinct  c968e235373e3a2e1bd50f6466aa5df36824cc03cf6c3df91c7c2577b6a6f3ad
scripted      10,061 frames  8,901 distinct  b68151b059b4396dd5cd760752a02b326afa566bc4e24d176661cc89e9fe83e4
scripted_alt  10,061 frames  8,173 distinct  77ce90940800de2613e11042581ce0a22a76a45b9bfda3591ff52a516ebfeed0
Result: PASS
```

This is approximately 2 minutes 50 seconds of generated gameplay per pattern
at 59.1894 Hz and took approximately 11 hours 39 minutes of wall time with the
three patterns running concurrently. Repeated P1/P2 Coin, Start, movement,
jump, and bubble-fire inputs were active in both scripted seeds. The preserved
frame-1,440 preview confirms real two-player Round 1 gameplay.

The supervising desktop shell ended after launching the named Docker workers,
so its final four small `result.txt` writes did not run. The workers continued
to the exact terminal frame window. The summaries were recovered only after
revalidating the canonical ROM and commits, hexadecimal stream format, exact
A/B byte equality, frame count, distinct-frame count, terminal PPM equality,
and final audio/framerate artifacts. No simulation output was altered.

### Remaining unavailable inputs

```text
POCKET_A_SD_ROOT: not mounted/supplied
POCKET_B_SD_ROOT: not mounted/supplied
Pocket A/B firmware and physical IDs: not yet recorded
SD-card identifiers: not yet recorded
Cable type/model: not yet recorded
```

### Next exact command

Commit the packaging/evidence milestone so the package source tree is clean,
then import the passing private run into the final ROM-free bundle:

```bash
source /home/borjaburgos/Developer/JOTEGO/private/link2p.env
export LINK2P_DETERMINISM_RESULTS=/home/borjaburgos/Developer/JOTEGO/private/JTBUBL-Link2P/simulation/determinism/long-8f48f41158aa-VGrO0G
make link2p-package ROM="$LOCAL_BUBBLE_BOBBLE_ROM" OUT="$PRIVATE_ARTIFACT_ROOT"
```

### Hardware status

Not started. The remaining local gates are clean final packaging, checksum
verification, and two temporary-card installs. No physical transport or
gameplay success is claimed.

## 2026-08-28 — first physical transport and handheld launch-boundary fix

### Physical result

- Both Pockets run firmware 2.6 with 32 GB SD UUIDs `0403-0201` and
  `D9C0-15E7`; the 64 GB card remained out of scope.
- APF metadata length violations in the first diagnostic package were fixed in
  superproject commit `77cad1ef9`, after which both diagnostic roles loaded
  normally through openFPGA.
- The physical Host and Join screens simultaneously showed their distinct
  role grids and green peer borders. This proves bidirectional physical packet
  framing and valid packet CRC reception.
- Both status bands remained cyan instead of turning green. The peers reached
  the armed/pending launch states but never entered `RUN`; gameplay was not
  attempted.
- Private photo evidence is preserved under
  `<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/hardware/2026-08-28/IMG_9670.jpeg`,
  SHA-256
  `2e6d4d18fc1b3360e7936f2869e0a12b92b21fcb3bfeb88eb9ac263475451fcc`.

### Root cause and correction

The target used the Pocket top-level `vblank` input as the launch boundary.
That input is documented in the target source as Dock-driven and did not pulse
on either handheld Pocket, leaving Host at `ST_BOUNDARY` and Join at
`ST_ARMED`. Link2P now uses the blank interval from its always-running local
diagnostic video timer. The protocol port was renamed from `ext_vblank` to
`launch_vblank` so the requirement is explicit.

The protocol test now drives independently phased Host and Join launch
boundaries, including reversed release order during reconnect. All five
Link2P unit tests and integrated Pocket lint pass. Corrected Diagnostic Host
and Join Quartus builds pass seed 0 with +0.119 ns and +0.122 ns worst slack;
their RBF SHA-256 values are
`a35f27dcec68a83ba479f28ecd81f9a8b21c0e8c09c0bcf342ceb5f4a9a4abd5`
and `c7f28b0437d74be131017b8eac176cc3d8a00465e1619f395b8b0a9fdff266ac`.
The corrected packages were installed on both 32 GB cards for a second
physical run on 2026-08-29.

## 2026-08-29 — corrected physical session launch

- Black Pocket ran Diagnostic Host; white Pocket ran Diagnostic Join.
- Both status bands changed to solid green simultaneously, confirming that
  both endpoints completed the launch handshake and entered `RUN`.
- Both peer borders remained green, confirming continued valid packet
  reception in both directions. The role-colored grids remained correct and
  neither endpoint displayed a red fault band.
- Private photo evidence is preserved under
  `<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/hardware/2026-08-29/IMG_9671.jpeg`,
  SHA-256
  `ba66a1e66ab3ec4496b6f174c693f98be9743ae3e1e7c1ae5c2666df3cb9ae84`.
- Session launch is now a physical PASS. Local-input indication remains to be
  exercised. The disconnect/reconnect check exposed a recovery race: Host
  stabilized with a green peer border/red status band while Join stabilized
  with a green peer border/magenta status band. Valid packets were flowing,
  but Host had advanced to fresh HELLO while Join remained in RECOVER.
- The source correction allows a recovering Join to accept a valid fresh Host
  HELLO when staggered cable contacts cause it to miss Host's WAIT packet. The
  protocol test now forces this exact contact ordering; all five Link2P unit
  tests pass.
- Corrected recovery Diagnostic Host and Join builds from JTCORES
  `2e5ef55bd650d3b601870a7f7f8e185235ce8d90` and Pocket target
  `23429334326fbf3211a6fe42e8939e9dca969d6a` pass seed 0 with +0.117 ns and
  +0.100 ns worst slack. Their RBF SHA-256 values are
  `62e90b4b21c5c09663395825127d72239cd368f9759e772bdbe974f107882564`
  and `ecb1a89ef9051282b47b68f23fbf416277d9ad1ee0f84b3a27cd4a53b7738942`.
- The private `2e5ef55` bundle passes all 127 recorded SHA-256 checks. Both
  corrected diagnostic roles were installed and read-back hash verified on
  32 GB SD UUIDs `D9C0-15E7` and `0403-0201`; the 64 GB card remained out of
  scope.

## 2026-08-30 — physical diagnostic transport gate passed

- White Pocket ran corrected Diagnostic Join/P2 and black Pocket ran
  corrected Diagnostic Host/P1. Both reached solid-green status bands and
  green peer borders.
- D-pad directions, A, B, Select, and Start changed the local-input row on
  both systems while the link remained green.
- After a two-second cable disconnect, reconnecting without relaunching either
  core automatically restored solid-green bands and borders on both systems.
- The physical diagnostic transport gate is complete. Corrected normal
  Host/P1 and Join/P2 synthesis and installation are next; real gameplay has
  not yet started.

### Normal gameplay builds

- Corrected normal Host/P1 and Join/P2 builds from JTCORES
  `b51ee9359944abad1d8c286cc02d4a1ef10ef6a1` and Pocket target
  `23429334326fbf3211a6fe42e8939e9dca969d6a` pass seed 0 with +0.121 ns and
  +0.120 ns worst slack.
- Normal Host and Join RBF SHA-256 values are
  `ce53976ad6b241888bc70c48c67e5ac7ee98b9ff9428abc00aeedd1fd62ed9b9`
  and `9f416fb249139c1bbf54e72447bf72b04d9bea71b779dcab6b56b4cf30bb8e01`.
- Combined private bundle `257a4c5` passes all 127 recorded SHA-256 checks.
  Both normal roles and their canonical ROM were installed and read-back hash
  verified on 32 GB SD UUIDs `D9C0-15E7` and `0403-0201`; the 64 GB card
  remained out of scope. Linked gameplay remains pending.
