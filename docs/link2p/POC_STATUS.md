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

This target will be added with the ROM-free transport RTL and testbench.
