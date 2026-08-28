# Link2P results

## Stock baseline

Status: verified through synthesis; not yet tested on a Pocket in this worktree.

```text
JTCORES commit: 1268a90e365c2520b412f224ae30d20c61aa0031
Pocket target commit: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
Quartus: Prime Lite 20.1.1 Build 720
Device: 5CEBA4F23C8
Result: PASS (0 errors, 236 warnings)
Logic: 8,765 / 18,480 ALMs (47%)
Registers: 8,429
Block memory: 348,581 / 3,153,920 bits (11%)
RAM blocks: 70 / 308 (23%)
DSP blocks: 26 / 66 (39%)
PLLs: 4 / 4 (100%)
Worst reported slack: +0.120 ns
RBF SHA-256: 51585dc51aa123cf6a7b93208e884ff386cd6801d948014b9c49bcd04860258e
```

The stock warning baseline contains no `Critical Warning`. It includes three derived clocks without explicit clock assignments and the target's existing unconstrained external I/O ports. Link2P SCK/SI/SO paths require explicit review and constraints; unrelated baseline warnings are not treated as new Link2P regressions.

Private preserved baseline:

```text
<PRIVATE_ARTIFACT_ROOT>/baselines/stock-1268a90-pocket-2050ac4/
```

## Link transport

Not yet verified.

## Dual-instance determinism

Not yet verified; requires the local Bubble Bobble ROM.

## Physical hardware

Not yet verified; requires two Pockets, SD cards, cable, and ROM.
