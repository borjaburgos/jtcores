# Link2P hardware test

## Required equipment

- Two Analogue Pockets.
- Two backed-up SD cards.
- A known-compatible GB/GBC link cable.
- Identical assembled Bubble Bobble ROM files on both cards.
- Link2P Host and Join packages plus the retained stock JTBUBL package.

Record Pocket firmware, a physical Pocket identifier, SD identifier, cable type, package hashes, ROM hashes, DIP settings, and display settings in `RESULTS.md`.

## Transport gate

Do not begin linked JTBUBL gameplay until the ROM-free transport diagnostic passes in both directions on hardware. Verify counters, local button bitmaps, CRC error count, timeout behavior, and a clean fresh session after disconnect/reconnect.

Build `link2p-diag-host` and `link2p-diag-join` for this gate. The screen uses
a green border after a framed peer is observed, a role-colored checkerboard,
a state/fault band, and bit rows for session, logical frame, TX/RX sequence,
local controls, CRC errors, and timeouts. Both diagnostic packages still contain
a complete local JTBUBL core; they only keep the target status video selected.

## Gameplay sequence

1. Back up both cards. Run the install helper with `--dry-run`, review it, then
   install both unique packages on each card without replacing stock JTBUBL.
2. Verify identical ROM SHA-256 and DIP settings.
3. Connect the cable; launch Join/P2, then Host/P1.
4. Confirm both remain waiting/reset until the peer is ready, then both leave reset.
5. Compare attract mode; insert P1 coin on Host and P2 coin on Join; start two-player play.
6. Confirm Host controls only P1, Join controls only P2, and both screens show the complete identical game.
7. Exercise simultaneous movement/actions, death/respawn, level transitions, bonus appearance/pickup, scores, and lives.
8. Play at least three levels and leave a longer attract/gameplay run while observing frame/CRC diagnostics.
9. Remove the cable during gameplay and confirm both stop/reset safely.
10. Reconnect, establish a fresh session, swap physical Host/Join units, and repeat a shorter run.

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
