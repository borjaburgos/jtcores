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

## Diagnostic Link2P synthesis

Status: both always-visible transport-diagnostic roles pass full Quartus
analysis, synthesis, fitting, assembly, and timing. These builds contain the
same complete local JTBUBL implementation as the normal roles; only the target
video selection keeps the diagnostic grid visible for physical cable bring-up.

```text
JTCORES commit: 8f48f41158aa45eddee17e2ad28d06e72858d679
Pocket target commit: ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e
Quartus: Prime Lite 20.1.1 Build 720
Device: 5CEBA4F23C8

Diagnostic Host seed 0: PASS, +0.090 ns worst slack
Diagnostic Host logic/registers: 9,573 ALMs (52%) / 9,670 registers
Diagnostic Host RBF SHA-256: 9a423870c5f9728c957f4a909b6da9cbc0c166398eafe9357938c2d723ebb0ce

Diagnostic Join seed 0: PASS, +0.096 ns worst slack
Diagnostic Join logic/registers: 9,584 ALMs (52%) / 9,628 registers
Diagnostic Join RBF SHA-256: acee8ddb27d5d963cdc24dba0bfc9cae1035a9b44dfea470ec85b779e0325d98
```

Both roles use 348,587 memory bits, 70 RAM blocks, 26 DSP blocks, and four
PLLs. The only Critical Warning is the inherited `c4` named-port PLL warning
already present in the stock baseline. The scoped SDC covers the asynchronous
cable pins and first synchronizer stages; SCK/SI/SO do not appear in the
unconstrained-port lists. Reports and ROM-free source packages are preserved at
`<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/work/diagnostic/{host,join}/`.

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
window.

A short qualification of the alternate timing also passes for both neutral
and scripted inputs: ROM transfer completes normally, both cores remain in a
common reset for 100 ms after transfer, and 63 paired frames per pattern are
identical with two distinct CRCs. This validates the delayed-reset and private
live-preview plumbing; it is not a substitute for the 10,000-frame gate.
The final long-run cabinet schedules wait 720 post-reset frames, then repeat P1
Select/coin, P2 coin, both Start buttons, and two-player movement/action pulses
every 240 frames so the run exercises live gameplay rather than only the boot
or attract sequence. The second seed reverses Start order and changes both
players' movement/action phases. The primary scripted preview at paired frame
1,440 visibly reached Round 1 with both player
sprites, enemies, and bubbles on the board. Its A/B PPMs had identical SHA-256
`439e02192ba84bca41bd826d9535b6b4c4086399716f328f55a0f0925aedfb6c`,
confirming live game entry and input exercise.

The three-pattern 10,000-frame gate passes. All patterns ran concurrently,
each with two complete JTBUBL instances, DIP value `ffff`, and a common 100 ms
post-download reset hold. Each produced 10,061 paired CRCs because the terminal
frame boundary follows the requested 10,000-frame window. The generated game
rate is 59.1894 Hz. A/B CRC files and final A/B frame images are byte-identical
within every pattern; each stream has thousands of distinct CRCs and is not
frozen.

```text
Pattern        Paired frames  Distinct CRCs  CRC-stream SHA-256
neutral               10,061          5,008  c968e235373e3a2e1bd50f6466aa5df36824cc03cf6c3df91c7c2577b6a6f3ad
scripted              10,061          8,901  b68151b059b4396dd5cd760752a02b326afa566bc4e24d176661cc89e9fe83e4
scripted_alt          10,061          8,173  77ce90940800de2613e11042581ce0a22a76a45b9bfda3591ff52a516ebfeed0
Result: PASS
```

The run used JTCORES commit
`8f48f41158aa45eddee17e2ad28d06e72858d679` and Pocket target commit
`ccb61e54625e5cb1a49a92a830c4bbfe3d631f1e`. Its wall-clock execution took
approximately 11 hours 39 minutes; the three patterns ran in parallel.

## Physical hardware

### First diagnostic bring-up, 2026-08-28

Both physical Pockets run firmware 2.6. The two 32 GB cards are identified by
UUID `0403-0201` and `D9C0-15E7`; the 64 GB card was excluded. Both cards
loaded the diagnostic Host and Join packages with the canonical ROM SHA-256
`529a46c61e96419cdc307c8bb9116c454eea60ab9a10673ae2be16282be53e80`.

The first package attempt exposed APF metadata fields beyond their documented
length limits. Corrected package commit `77cad1ef9` shortened platform IDs,
platform names, bitstream names, and bitstream filenames, and made the core
folder match `metadata.shortname`. Both roles then loaded through openFPGA.

Photo evidence shows the physical Host red/blue role grid and Join green/blue
role grid simultaneously. Both borders are green, proving that each endpoint
received a correctly framed peer packet over the physical link cable. Neither
screen shows a red fault band. The inner status bands remain cyan, however,
which means both endpoints are armed/pending and have not entered `RUN`.

```text
Physical serial/framing path: PASS in both directions
Peer header and packet CRC: PASS in both directions
Role distinction: PASS
Session launch: FAIL, stable cyan armed/pending state
Gameplay: not started
Evidence SHA-256: 2e6d4d18fc1b3360e7936f2869e0a12b92b21fcb3bfeb88eb9ac263475451fcc
```

The stall was traced to `jtframe_pocket_top.v` wiring the launch gate to the
Pocket top-level `vblank` input, which is Dock-driven and remains idle in this
handheld setup. The correction uses the always-running Link2P diagnostic
timer's local blanking interval instead. Unit coverage now phases Host and
Join launch boundaries independently to model two undocked Pockets. The full
five-test Link2P suite and integrated Pocket lint pass.

Corrected diagnostic synthesis also passes from JTCORES commit
`1fd09c44d5f0e8b52ce4caccf897f0668f8b15d0` and Pocket target commit
`17657ea933cb28dba975fc01025105dcf257ac03`:

```text
Host seed 0: PASS, +0.119 ns, 9,575 ALMs / 9,660 registers
Host RBF SHA-256: a35f27dcec68a83ba479f28ecd81f9a8b21c0e8c09c0bcf342ceb5f4a9a4abd5
Join seed 0: PASS, +0.122 ns, 9,563 ALMs / 9,580 registers
Join RBF SHA-256: c7f28b0437d74be131017b8eac176cc3d8a00465e1619f395b8b0a9fdff266ac
```

### Corrected diagnostic bring-up, 2026-08-29

The corrected Host package ran on the black Pocket and the corrected Join
package ran on the white Pocket. Both displays simultaneously showed solid
green status bands and green peer borders. The green status bands confirm
that both endpoints completed the launch handshake and entered `RUN`; the
green borders confirm continued valid peer-packet reception. The role-colored
grids remained distinct and neither display showed a red fault band.

```text
Physical serial/framing path: PASS in both directions
Peer header and packet CRC: PASS in both directions
Role distinction: PASS
Session launch: PASS on both endpoints
Local-input display exercise: pending
Disconnect/reconnect recovery: FAIL in installed build; recovery race reproduced
Gameplay: not started
Evidence SHA-256: ba66a1e66ab3ec4496b6f174c693f98be9743ae3e1e7c1ae5c2666df3cb9ae84
```

The evidence photo is preserved privately at
`<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/hardware/2026-08-29/IMG_9671.jpeg`.
On cable reconnect, Host stabilized with a green peer border and red status
band while Join stabilized with a green peer border and magenta status band.
Those indicators identify Host in fresh HELLO with a latched prior fault and
Join still in RECOVER: valid packets were flowing, but the peers were
deadlocked at different recovery steps. This can happen when cable contacts
reconnect at different times: Host consumes Join's WAIT before Join recovers
framing, advances to HELLO, and the installed Join accepts only WAIT while in
RECOVER.

The source correction lets a recovering Join accept a valid fresh Host HELLO.
The protocol regression now reconnects clock and Join-to-Host data before the
Host-to-Join data contact to force the observed ordering. All five Link2P unit
tests pass with this adversarial case.

Corrected recovery synthesis passes from JTCORES commit
`2e5ef55bd650d3b601870a7f7f8e185235ce8d90` and Pocket target commit
`23429334326fbf3211a6fe42e8939e9dca969d6a`:

```text
Host seed 0: PASS, +0.117 ns, 9,598 ALMs / 9,645 registers
Host RBF SHA-256: 62e90b4b21c5c09663395825127d72239cd368f9759e772bdbe974f107882564
Join seed 0: PASS, +0.100 ns, 9,561 ALMs / 9,612 registers
Join RBF SHA-256: ecb1a89ef9051282b47b68f23fbf416277d9ad1ee0f84b3a27cd4a53b7738942
```

The ROM-free private bundle is preserved at
`<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/2e5ef55`; all 127 entries in its
`SHA256SUMS` pass. Both corrected diagnostic roles were installed and
read-back hash verified on 32 GB SD UUIDs `D9C0-15E7` and `0403-0201`; the
64 GB card remained excluded.

### Corrected recovery retest, 2026-08-30

The white Pocket ran Join/P2 and the black Pocket ran Host/P1. Both reached
solid-green status bands and green peer borders. D-pad directions, A, B,
Select, and Start changed the local-input row on both systems without a fault.
After a two-second cable disconnect, reconnecting without exiting either core
automatically returned both endpoints to solid-green status bands and green
peer borders.

```text
Corrected package startup: PASS on both endpoints
Local-input display exercise: PASS on both endpoints
Disconnect fault/reset behavior: PASS
Automatic fresh-session reconnect: PASS
Diagnostic physical transport gate: PASS
Gameplay: not started
```

Normal Host/P1 and Join/P2 gameplay packages may now be built and installed
for the real-gameplay phase.

### Corrected normal gameplay synthesis, 2026-08-30

Normal Host/P1 and Join/P2 synthesis passes from JTCORES commit
`b51ee9359944abad1d8c286cc02d4a1ef10ef6a1` and Pocket target commit
`23429334326fbf3211a6fe42e8939e9dca969d6a`:

```text
Host seed 0: PASS, +0.121 ns, 9,607 ALMs / 9,650 registers
Host RBF SHA-256: ce53976ad6b241888bc70c48c67e5ac7ee98b9ff9428abc00aeedd1fd62ed9b9
Join seed 0: PASS, +0.120 ns, 9,575 ALMs / 9,721 registers
Join RBF SHA-256: 9f416fb249139c1bbf54e72447bf72b04d9bea71b779dcab6b56b4cf30bb8e01
```

The combined ROM-free private bundle is preserved at
`<PRIVATE_ARTIFACT_ROOT>/JTBUBL-Link2P/257a4c5`; all 127 entries in its
`SHA256SUMS` pass. Both normal roles and their canonical ROM were installed
and read-back hash verified on 32 GB SD UUIDs `D9C0-15E7` and `0403-0201`;
the 64 GB card remained excluded.

### First linked gameplay run, 2026-08-30

The white Pocket ran Join/P2 and the black Pocket ran Host/P1. Both displayed
the complete local Bubble Bobble game, accepted credits through Select, and
entered linked two-player gameplay through at least the Level 1 to Level 2
transition. The user reported continued synchronized gameplay after that
transition. Exiting and cleanly relaunching Join followed by Host also restored
a playable linked session.

```text
Complete local game video on both Pockets: PASS
Credits and Start: PASS on a clean session
Linked two-player gameplay: PASS through at least Level 2
Level transition: PASS
Cable removal safe reset/debug screen: PASS
Seamless live-game reconnect: unsupported POC non-goal
```

Removing the cable during gameplay safely selected the diagnostic screen.
Reconnecting returned both cores to the NOTICE screen, but the automatically
recovered game instance could not start: credits accumulated, then Start
returned to NOTICE. Exiting both cores and launching Join followed by Host
restored normal gameplay. For that revision, the recovery procedure after any
cable loss was therefore to reconnect the cable and relaunch both roles.

The protocol regression now phases the two game-frame inputs independently
and verifies neutral, Coin, and Start after a staggered-contact reconnect and
game reset. All five unit tests pass. This shows that the abstract link/input
pipeline recovers; it does not model JTBUBL's complete mid-game reset state.
The exact game-level reinitialization cause remains unresolved, but seamless
reconnection during a live game is an explicit non-goal for this POC.

### Corrected automatic clean restart, 2026-08-30

The relaunch-only result above was superseded after isolating state that the
transport reset did not clear. CPU reset left the 8 KiB JTBUBL work RAM and
1 KiB MCU communication RAM intact; a complete core relaunch had implicitly
reinitialized those FPGA memories. Link2P now scrubs both memories while cable
reset is held and resets the retained VBL edge state. Stock JTBUBL behavior is
unchanged.

All six ROM-free tests pass, including a targeted JTBUBL clean-restart RAM
test. The protocol test also verifies neutral input, Coin, and Start after a
staggered-contact reconnect. Complete Pocket Link2P lint passes.

Corrected normal Host/P1 and Join/P2 builds use JTCORES commit
`4febce354fd57d03aa7904c4b061268ef5f5775a` and Pocket target commit
`10e9d6a5f13a0eec763000013ca30c2014e7a0a0`:

```text
Host seed 0: PASS, +0.109 ns
Host RBF SHA-256: 217d1e2f9416817f14b6a0caf5213fbb589523d5d7f4c45386e54c80b35894d6
Join seed 0: PASS, +0.112 ns
Join RBF SHA-256: 71d59cd27a47e31095e17acca32776780ecbb8eae07b4d7ad79c9ed8dcacdd6a
```

Private bundle `4febce3` passes all 127 entries in `SHA256SUMS`. Corrected
Join/P2 and Host/P1 plus the canonical external ROM were installed and
read-back hash verified on White 32 GB UUID `D9C0-15E7` and Black 32 GB UUID
`0403-0201`; the 64 GB card remained excluded.

The physical retest started a four-credit linked game normally. Cable removal
during gameplay moved both endpoints to the diagnostic/reset screen. After
reconnect, both returned to a clean NOTICE screen and Select plus Start began
a new linked game without exiting either core.

```text
Corrected package startup and credits/Start: PASS
Cable removal safe reset/debug screen: PASS
Automatic clean restart after reconnect: PASS
Post-reconnect credits/Start without core relaunch: PASS
Live-game progress preservation: unsupported future enhancement
```

The supported first-release policy is a clean automatic restart after cable
loss. The interrupted game's progress is intentionally discarded; the build
does not claim seamless preservation or resumption of live gameplay.

### Final POC code review and synthesis, 2026-08-31

A complete review of the Link2P RTL, timing constraints, target integration,
tests, build scripts, packaging, installer, and documentation produced a small
set of defensive refinements:

- Stock JTBUBL again retains its original VBL reset logic; the clean-restart
  initialization remains guarded by `JTFRAME_LINK2P`.
- A valid packet arriving exactly at the peer-timeout boundary now wins over
  the timeout decision. A regression test covers that cycle.
- Fresh sessions clear every input-buffer slot and stale session diagnostics.
- Preserved role/link state is connected to the Pocket top for SignalTap and
  the diagnostic video path.
- The Pocket SDC now names the actual launch-VBL synchronizer.
- Builds refuse dirty or mismatched submodule source, preserve the reports for
  the released seed, and record that seed. Packaging rejects mixed source
  revisions across the four roles.

All six ROM-free tests pass. Link2P Host, Link2P Join, and stock JTBUBL Pocket
lint pass; the remaining pin/PLL warnings are pre-existing JTFRAME warnings
also present in earlier builds.

The reviewed role builds use JTCORES commit
`b9f54d0b95c4e0f77e870b4b5cb606877e0c9199` and Pocket target commit
`65a1b9d6434fb4d70e64e44c64ff4044cbabb183`:

```text
Normal Host seed 0: PASS, +0.120 ns
Normal Host RBF SHA-256: 4f5d3b42b8fdbb3781975994a9ab4a9dad7c961c154199321b727469431ec78b
Normal Join seed 0: PASS, +0.122 ns
Normal Join RBF SHA-256: 6a0bae65cf2563cec806382237cb8bce901f129214556b429c2a8b6c7021a456
Diagnostic Host seed 0: PASS, +0.121 ns
Diagnostic Host RBF SHA-256: f728a7ff1e92ebc5a334c49831a1eba8e8026b35a96af0601b78f80fa07ecd64
Diagnostic Join seed 0: PASS, +0.121 ns
Diagnostic Join RBF SHA-256: 96a10c992d3e7492694dcbf92bd7cb0681a9b5a6f66ac27885fc27a6a9fbd275
```

The prior normal Host/Join revision remains the latest physical gameplay and
disconnect/restart PASS. These reviewed bitstreams require one final two-Pocket
smoke test after installation; no new live-game reconnection claim is made.

### Refreshed SD installation, 2026-08-31

The reviewed normal roles were installed on the same backed-up 32 GB cards:

```text
Black UUID 0403-0201: normal Host, read-back SHA-256 PASS
White UUID D9C0-15E7: normal Join, read-back SHA-256 PASS
Canonical external ROM on both cards: read-back SHA-256 PASS
64 GB card: excluded
```

The black card's device was writable but its automatic filesystem mount was
read-only. A UUID-addressed UDisks unmount/remount with `rw,flush` restored
write access without `sudo`; the same procedure is now documented in the build
guide. Both cards were synchronized and safely unmounted after verification.
The refreshed pair is ready for its final physical smoke test.
