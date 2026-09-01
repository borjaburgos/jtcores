# Link2P hardware test

## Required equipment

- Two Analogue Pockets.
- Two backed-up SD cards.
- A known-compatible GB/GBC link cable.
- Identical assembled Bubble Bobble ROM files on both cards.
- Link2P normal and diagnostic Host/Join packages plus the retained stock
  JTBUBL package.

Record Pocket firmware, a physical Pocket identifier, SD identifier, cable type, package hashes, ROM hashes, DIP settings, and display settings in `RESULTS.md`.

## Transport gate

Do not begin linked JTBUBL gameplay until the ROM-free transport diagnostic passes in both directions on hardware. Verify counters, local button bitmaps, CRC error count, timeout behavior, and a clean fresh session after disconnect/reconnect.

Build `link2p-diag-host` and `link2p-diag-join` for this gate, or install them
from the final bundle with `--mode diagnostic`. The screen uses a green border
after a framed peer is observed, a role-colored checkerboard, a state/fault
band, and bit rows for session, logical frame, TX/RX sequence, local controls,
CRC errors, and timeouts. Both diagnostic packages still contain a complete
local JTBUBL core; they only keep the target status video selected. They use
different core/platform IDs from both normal Link2P roles and stock JTBUBL.

## Gameplay sequence

1. Back up both cards. Run the install helper with `--mode diagnostic`,
   `--dry-run`, and `--role both`; review it, then install both diagnostic roles
   on each card without replacing stock JTBUBL.
2. Verify identical ROM SHA-256 and DIP settings.
3. Connect the cable; launch diagnostic Join/P2, then diagnostic Host/P1.
4. Confirm both remain waiting/reset until the peer is ready, then both leave
   reset. Exercise each local control and verify the corresponding diagnostic
   bits and clean CRC/timeout counters.
5. With both units handled as they would be during play, run the diagnostic
   pair for at least 15 minutes with each available cable. Record starting and
   ending CRC-error and timeout rows. Any spontaneous session reset fails the
   transport gate; preserve the counter deltas and cable identity.
6. Disconnect/reconnect once, verify a clean fresh diagnostic session, then
   install both normal roles on each card with `--mode normal`.
7. Launch normal Join/P2, then normal Host/P1 and compare attract mode.
8. Press Select to insert P1 credits on Host and P2 credits on Join, then press
   Start as needed to enter real two-player gameplay.
9. Confirm Host controls only P1, Join controls only P2, and both screens show
   the complete identical game.
10. Exercise simultaneous movement/actions, death/respawn, level transitions,
   bonus appearance/pickup, scores, and lives.
11. Play at least three levels and leave a longer attract/gameplay run while
    observing frame/CRC diagnostics.
12. Remove the cable during gameplay and confirm both stop/reset safely.
13. Reconnect without exiting either core and confirm both return to a clean
    NOTICE screen. Insert credits with Select and press Start; a new linked
    game must start normally. The interrupted game's progress is intentionally
    discarded; preserving or resuming live gameplay is not a POC requirement.
14. Swap physical Host/Join units and repeat a shorter run.

## Failure evidence

For a failure, capture only:

```text
Did both Pockets leave reset?
Did they show the same attract screen?
Did Host control P1 and Join control P2?
First visible divergence
Local/peer frame counters and CRCs
CRC/timeout/error counters
Behavior after cable removal
Photo or video of both screens
```
