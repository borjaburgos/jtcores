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

Version 2 additionally preserves the last fault across automatic recovery:
the four-bit row at y=32–39 is 1 role, 2 identity, 3 peer/session, 4 timeout,
5 input, or 6 video. Bits are MSB first from the left. The rows at y=184–199
and y=208–223 show recovered-history inputs and missed input deadlines,
respectively. Counters saturate and survive session restarts, but not core
reload. A code-5 reset without a deadline increment points to a conflicting
input or buffer-window problem. Photograph both units: one may only report
the other unit's fault (code 3).

Use matching protocol-2/build-`0x4c325003` packages on both Pockets. Before
testing, record the counters; after each unexpected reset, record them again
without exiting the core. A rising damaged-packet count with no reset is a
successful tolerated error, not by itself a failed session. A rising recovered
count shows that a previous input supplied missing history. Neither establishes
whether the electrical cause was a cable contact, noise, or another fault.

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
13. Reconnect after a sustained loss, without exiting either core, and confirm both return to a clean
    NOTICE screen. Insert credits with Select and press Start; a new linked
    game must start normally. The interrupted game's progress is intentionally
    discarded. Brief self-recovering interruptions are now expected to be
    tolerated if inputs arrive before their deadlines; a manual unplug is not
    an accurate millisecond-duration test and may legitimately cause a reset.
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
