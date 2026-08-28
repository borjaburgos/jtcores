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

## Final ROM-free Link2P synthesis

Status: Host and Join verified through full Quartus analysis, synthesis,
fitting, assembly, and timing from the coordinated, clean source commits.

```text
JTCORES commit: 162c6fc41dc5d54ce2174b66153cc80c3b99e3ef
Pocket target commit: ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e
JTCORES upstream master at verification: 47e6b8dad5b52b6f314813fe3d78807dcce77757
Pocket upstream master at verification: 2050ac4d09d126ab1af5ad7eba48ef4426804a3f
Quartus: Prime Lite 20.1.1 Build 720
Device: 5CEBA4F23C8

Host seed 0: PASS, +0.119 ns worst slack
Host logic/registers: 9,596 ALMs (52%) / 9,726 registers
Host RBF SHA-256: e094638f014d0afce836520d70d850cb5fee3b09c25d5106ae2334181a8fec9f
Host pins: SI input, SCK output, SO output

Join seed 0: PASS, +0.119 ns worst slack
Join logic/registers: 9,586 ALMs (52%) / 9,682 registers
Join RBF SHA-256: 6382241d35112bf5be01bf21bb4cdc8e5056378ed07b5213a2e93a87fb962b2d
Join pins: SI input, SCK input, SO output
```

Both roles use 348,587 memory bits, 70 RAM blocks, 26 DSP blocks, and
four PLLs. The narrowly scoped cable CDC exceptions match the physical link
ports and first synchronizer stages; SCK/SI/SO do not appear in Quartus's
unconstrained-port list. No Link2P latch, gated-clock, CDC-attribute, or unused
signal warning remains.

The release-candidate role packages and complete Quartus reports are preserved
outside Git at:

```text
<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/work/normal/host/
<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/work/normal/join/
```

## Stock post-change regression

A no-Link2P build passes with all link output enables permanently disabled and
no Link2P hierarchy instantiated. Its `b5d437f` embedded version produces RBF
SHA-256 `ed5d810807c28626deee302f82c0656e6ff70c43aeadbe45e1cabffdc4518f23`
and +0.109 ns worst slack. It differs from the original baseline hash because
JTFRAME embeds the current Git commit; it remains the stock package ID and does
not enable the new target path.

## Dual-instance determinism

The canonical assembled Bubble Bobble Japan Ver 0.1 ROM was validated outside
Git before simulation:

```text
Size: 786,692 bytes
CRC-32: 2d09cf0e
MD5: fcbcd7500f6a7421e827373cfa8890d3
SHA-256: 529a46c61e96419cdc307c8bb9116c454eea60ab9a10673ae2be16282be53e80
```

The 600-frame scripted smoke gate passes using two complete JTBUBL instances
in one Verilator model. Each instance has independent writable CPU, MCU,
palette, video, object, and work RAM; both read the same immutable ROM image.
The harness applies identical ROM download, DIP value `ffff`, reset, and P1/P2
cabinet inputs. It compares video timing and active pixels cycle by cycle,
audio sample outputs cycle by cycle, and CRC-32 over every completed active
frame.

```text
Requested post-download frames: 600
Recorded paired frames: 601 (includes terminal boundary frame)
A/B CRC streams: identical
Distinct frame CRCs: 2
CRC-stream SHA-256: 1d568192333ac80f75f559c92354ee3dc0d793c9f783af20776b4df6593b8a80
Result: PASS
```

The two MCU reset-release messages occurred together at the end of the smoke
window. The required 10,000-frame neutral and scripted runs are still in
progress/pending; no long-run or bonus-behavior result is claimed yet.

A short qualification of the alternate timing also passes for both neutral
and scripted inputs: ROM transfer completes normally, both cores remain in a
common reset for 100 ms after transfer, and 63 paired frames per pattern are
identical with two distinct CRCs. This validates the delayed-reset and private
live-preview plumbing; it is not a substitute for the 10,000-frame gate.
The final long-run cabinet schedules wait 720 post-reset frames, then repeat P1
Select/coin, P2 coin, both Start buttons, and two-player movement/action pulses
every 240 frames so the run exercises live gameplay rather than only the boot
or attract sequence. The second seed reverses Start order and changes both
players' movement/action phases. Gameplay entry must also be confirmed from
the private frame previews before the physical gate is opened.

## Physical hardware

Not yet verified; requires two Pockets, SD cards, cable, and ROM.
