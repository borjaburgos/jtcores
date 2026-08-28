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
