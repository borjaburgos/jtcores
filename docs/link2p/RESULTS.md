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

The stock warning baseline includes an inherited `c4` named-port Critical
Warning in `jtframe_pllgame`; the same warning is present before and after
Link2P and is unrelated to the new target logic. It also includes three derived
clocks without explicit clock assignments and the target's existing
unconstrained external I/O ports. Unrelated baseline warnings are not treated
as new Link2P regressions.

Private preserved baseline:

```text
<PRIVATE_ARTIFACT_ROOT>/baselines/stock-1268a90-pocket-2050ac4/
```

## ROM-free transport simulation

Status: passing in Icarus Verilog 13.0 through `make link2p-unit`.

- Fixed-slot full-duplex transfer, valid CRC, corrupted-bit CRC rejection, and
  reset during a slot.
- Host-first, Join-first, near-simultaneous launch, late cable connection, and
  Join reset during handshake.
- Build mismatch, simulated Host/Host role conflict, and safe Join/Join wait.
- VBL handshake, exhaustive active-low joystick/action/Start/Coin mapping,
  symmetric two-frame delay, disconnect fault, and fresh-session reconnect.
- Duplicate sequence, stale sequence, and out-of-window/buffer-overflow fault
  injection.

Integrated JTBUBL lint passes with only the existing Analogizer missing-pin
warnings.

## Link2P synthesis checkpoint

Status: Host and Join verified through full Quartus analysis, synthesis,
fitting, assembly, and timing before the coordinated source commits. A final
post-commit rebuild is required for package hashes because JTFRAME embeds the
superproject commit ID.

```text
Quartus: Prime Lite 20.1.1 Build 720
Device: 5CEBA4F23C8

Host seed 0: PASS, +0.122 ns worst slack
Host logic/registers: 9,611 ALMs (52%) / 9,664 registers
Host RBF SHA-256 checkpoint: 674da07bca95980f41566793aef827be69a35bd5fec481070fae7af45a5279e6
Host pins: SI input, SCK output, SO output

Join seed 0: PASS, +0.122 ns worst slack
Join logic/registers: 9,591 ALMs (52%) / 9,668 registers
Join RBF SHA-256 checkpoint: 8e405ce628b8852062ff453d6179199557414e4b4699111643009b15b1487d45
Join pins: SI input, SCK input, SO output
```

Both roles use 348,587 memory bits, 70 RAM blocks, 26 DSP blocks, and
four PLLs. The narrowly scoped cable CDC exceptions match the physical link
ports and first synchronizer stages; SCK/SI/SO do not appear in Quartus's
unconstrained-port list. No Link2P latch, gated-clock, CDC-attribute, or unused
signal warning remains.

## Stock post-change regression

A no-Link2P build passes with all link output enables permanently disabled and
no Link2P hierarchy instantiated. Its `b5d437f` embedded version produces RBF
SHA-256 `ed5d810807c28626deee302f82c0656e6ff70c43aeadbe45e1cabffdc4518f23`
and +0.109 ns worst slack. It differs from the original baseline hash because
JTFRAME embeds the current Git commit; it remains the stock package ID and does
not enable the new target path.

## Dual-instance determinism

Not yet verified; requires the local Bubble Bobble ROM.

## Physical hardware

Not yet verified; requires two Pockets, SD cards, cable, and ROM.
