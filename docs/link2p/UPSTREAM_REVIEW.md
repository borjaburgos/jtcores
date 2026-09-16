# Upstream review preparation

## Preserved baseline

The hardware candidate remains `49991da`, protocol 2 / build `0x4c325003`.
The user reported diagnostics and real gameplay passing with the Analogue
cable. Duration, counter readings, level count, and role swaps were not
supplied. A later intermittent NOTICE/debug reboot loop after cable recovery
remains unresolved; it stopped reproducing reliably, but no fix was made.
Clean restart, endurance, and multi-cable validation remain open gates.

JTCORES `18d03b8a6` and Pocket `387949c` preserve the POC work, interruption
measurements, installation evidence, and this hardware report. Existing POC
history was not rewritten. No bitstream or SD-card content changed during
review preparation.

## First review slice: standalone transport

Pocket fork branch: [`borjaburgos/link2p-transport-review`](https://github.com/borjaburgos/pocket/tree/borjaburgos/link2p-transport-review),
commit `ad830ca`. [View the five-file diff](https://github.com/borjaburgos/pocket/compare/5a982f8a6fc74522cbe7e5e23219627f8ad054b6...ad830cad4419b45fd7060a206a9b3ab9008096c6).
It starts from upstream `5a982f8`, not the historical POC base. The separate
worktree is `../pocket-link2p-review` relative to the JTCORES checkout.
Its push destination is explicitly the user's `borjaburgos/pocket` origin;
it does not track an upstream branch for pushing. This review is shared as a
branch in the user's fork; no upstream PR has been opened. The separate
experimental binary handoff below contains the full POC, not this review slice.

| File | Lines | Purpose |
| --- | ---: | --- |
| `hdl/jtframe_pocket_link_serial.v` | 221 | Opaque, framed, full-duplex packets |
| `ver/link_serial/test.sv` | 176 | Asynchronous endpoint and fault tests |
| `ver/link_serial/crc_test.sv` | 69 | Independent checksum vectors |
| `ver/link_serial/sim.sh` | 24 | Standalone test entry point |
| `ver/link_serial/README.md` | 63 | Interface, timing, scope, limitations |

Total: **5 added files, 553 lines, one cohesive commit**. No existing upstream
file changes. The HDL is byte-identical to the tested candidate, SHA-256
`96888f92ddb038d66833c82a6d155f1e6132a08520e1e1df86bceca022b5f952`.
It is deliberately not in `cfg/files.yaml` or connected to pins yet; merging
this slice alone would not enable linked gameplay or affect stock builds.

### Completed validation

- Icarus: CRC-8 and CRC-32, accelerated divider 8.
- Verilator: both widths at production divider 96 / 250 kHz nominal SCK.
- Both widths: exact received packets, transmit updates during a slot, every
  packet bit corrupted in each direction, and phase-offset endpoint clocks
  with approximately 96 ppm relative frequency difference.
- Production CRC-32: all-contact interruption, each data direction alone,
  clock held low/high, and independent mid-slot resets of either endpoint.
- Independent vectors: correct checksum, the earlier damaged-tail collision,
  and an all-zero packet. Legacy CRC-8 accepts the latter two; CRC-32 rejects
  both. The new clock-loss test reproduced all-zero acceptance under CRC-8,
  so arbitrary-contact continuation is not claimed for that legacy format.
- The preserved POC's complete ROM-free unit suite passed again, including
  65,542 changing-input frames and dirty-RAM restart clearing.
- Patch whitespace checks and byte-for-byte HDL comparison passed.

Private logs: `JTBUBL-Link2P/review-transport-20260915-tMJS69` under the artifact
root. Initial overbroad CRC-8 continuation assertions are retained there as
failed probes; the final tests explicitly distinguish checksum limitations
from production CRC-32 requirements. No new Quartus build was needed for
this unconnected, unchanged HDL extraction; no newly synthesized hardware
is being claimed.

## Subsequent slices

1. **Session protocol:** identity, frame-keyed inputs, history, deadlines,
   reset handshake, and a compact protocol specification with focused tests.
   Keep this independent of Pocket pins and Bubble Bobble internals. Agree
   shared JTFRAME placement/API with JOTEGO before introducing another layout.
2. **Pocket integration:** adapter, explicit clock-crossing/timing constraints,
   input/reset wiring, and the minimum status support needed to diagnose it.
   Preserve upstream's newer core-mod/video changes. Rebuild and test stock
   and linked variants; any behavioral change needs a new hardware test.
3. **JTBUBL enablement:** the small configuration and guarded RAM-reset changes
   required for clean restart. Include the existing failure evidence and
   RAM-clear regression. Coordinate the Pocket dependency/submodule update.

Current JTCORES upstream was inspected at `e7958c86d`; no integration branch
has been prepared against it yet. These are proposed review boundaries, not
already-completed follow-up PRs. Ask JOTEGO whether to submit transport first
or use it as the first commit in a coordinated series before opening an
upstream PR.

## Experimental binary handoff — 2026-09-16

[ROM-free evaluation kit](https://github.com/borjaburgos/pocket/releases/tag/link2p-poc-49991da)
in the private Pocket fork; JOTEGO has access. Its tag points to the binary
Pocket source `d31d180`, not the transport-review branch. It contains the four
unchanged `49991da` bitstreams, package metadata, licenses, Spanish installation
and test instructions, and SHA-256 checksums. No ROM, firmware, private reports,
or SD-card data is included. The restart-loop limitation is explicit.

The allowlisted package reproduced byte-for-byte, passed extraction checks,
and was downloaded from GitHub and compared with the original upload. Both
standalone transport suites passed again on September 16 (Icarus divider 8,
Verilator divider 96, both CRC widths). This is a packaging/test refresh, not
a new synthesis, hardware playtest, or fix. The five-file review is unchanged.

Before proposing behavioral fixes, the next correctness pass should model
independent SDRAM for each game and preserve MCU RAM on reset as hardware does.
Then test real gameplay through cable loss, a new session, Select/Start, and
sustained post-restart gameplay. Capture the initiating fault on both Pockets
if the intermittent loop returns; passing unit tests alone does not close it.

## Kept outside the first PR

Development diaries, local dashboards, pause experiments, SD installation and
bundle automation, private paths/device records, ROMs, and generated artifacts
remain in the POC/fork or private evidence store. They are not discarded.
Pause/resume and automatic role selection remain separate future work.

The shared-memory gameplay harness still needs independent memory models
before we can make independent dual-game or pause-equivalence claims. That
work and documented sustained gameplay/restart tests are prerequisites for
stronger integration claims, not evidence supplied by the transport-only PR.
The simulation/hardware MCU RAM-reset discrepancy is also a coverage gap,
not a demonstrated explanation for the hardware reboot loop.

## Fork navigation and provenance

The full POC branches in both forks are now named
`borjaburgos/jtbubl-link2p-poc`. Their existing commit history is preserved;
dated development logs retain the original branch names. `master` remains
the untouched baseline. The full POC is not the proposed upstream diff.
JTCORES opens the full POC by default; Pocket opens the focused transport
review. Both forks' About links point to their review guides.
Its Pocket submodule URL points to `borjaburgos/pocket`, where the pinned POC
commits are published. That fork remains private; reviewers need access.
JOTEGO's access was verified. This fork-only URL change is not part of the
transport review or a proposed upstream configuration change.

The unpublished transport extraction `d82fa0a` was amended to `ad830ca` only
to add the new hardware limitation and Codex-assistance note to its guide.
Its HDL and executable tests are identical. These five documentation lines
are the difference between the original 548-line slice and the 553-line slice.
Link2P development by Borja Burgos with assistance from OpenAI Codex.
