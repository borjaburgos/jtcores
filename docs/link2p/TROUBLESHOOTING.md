# Link2P troubleshooting

## Session never leaves WAIT_FOR_PEER

- Confirm one Host and one Join package are running.
- Confirm the GB/GBC cable is fully seated and compatible.
- Check SCK activity from Host and confirm Join leaves SCK high impedance.
- Inspect peer timeout and CRC counters.
- Two Join packages are indistinguishable from a disconnected cable and intentionally remain waiting.
- Do not intentionally connect two Host builds: the RTL detects the role error
  in simulation, but two physical push-pull SCK drivers are an invalid setup.

## ROLE CONFLICT or BUILD/DIP mismatch

- Verify package role and RBF SHA-256.
- Verify protocol/build IDs and source commits in the manifest.
- Verify identical DIP settings.
- Power/reset both sessions and retry with a fresh session ID.
- If a fault is latched, leave the cable connected; both sides first exchange a
  quiet WAIT state, then the Host creates a new session and reset remains held
  until the next valid GO/VBL sequence.

## Input mismatch

- Confirm final controls are active low.
- Confirm Pocket's local controller is the source presented as JTFRAME player 1 before Link2P remapping.
- Check target logical frame, sequence, and both buffered player samples.
- Never bypass the frame buffer for local input.

## Frequent involuntary resets

- Confirm both role manifests report protocol version 2, build ID
  `0x4c325003`, and `serial_clock_hz` 250000. Do not mix them with the older
  protocol-1/250 kHz or 1 MHz packages.
- Run the always-visible diagnostic pair and record CRC-error and timeout
  counter deltas separately for each cable and physical Host/Join assignment.
- Compare the same two Pockets and cable with a known-good linked GB/GBC title.
  A failure there points to the physical cable/connector path; a stable stock
  link with failing Link2P diagnostics points back to the custom transport.
- A spontaneous reset is a failed stability test even if automatic restart
  succeeds. Do not treat clean recovery as evidence that the link is robust.

## DESYNC

Record the first logical frame and both fingerprints. Check, in order: ROM/DIP/build identity, reset release diagnostics, input frame/sequence, packet CRC/stale counters, uninitialized RAM, then MCU-visible state. Do not modify JTBUBL before target-level causes are disproven.

## NOTICE loop after a gameplay cable reconnect

Sustained cable loss intentionally stops both games and selects the diagnostic
screen. Recovery is intended to negotiate a fresh session, clear JTBUBL work
and MCU communication RAM, and permit a new game through Select and Start.
The interrupted game's progress is discarded; live-game resume is unsupported.

Candidate `49991da` / protocol 2 / build `0x4c325003` has an unresolved,
intermittent NOTICE/debug reboot loop after cable recovery. Select can still
register credits or advance the screen without reliably curing the loop.
Successful retries do not close the issue. See [RESULTS.md](RESULTS.md).

- Verify both normal-role manifests match the candidate; compare bitstream
  hashes against that bundle's `SHA256SUMS`, not an older release's hashes.
- Capture both screens through a loop before exiting the cores. In normal
  builds, the checkerboard reappearing means another link reset was requested.
- The first four cells immediately below the top status band show the last
  fault, most-significant bit first: 3 = peer fault, 4 = timeout, 5 = input
  fault, 6 = video mismatch. One endpoint may only show the propagated fault.
- Record whether cable removal occurred during gameplay or at NOTICE, and
  preserve role/build identity and the visible counters. Do not infer the
  initiating fault solely from Select still working.
- Exiting both cores and relaunching Join followed by Host is a fallback that
  previously restored gameplay, not a fix or a current reliability guarantee.

The MCU's internal RAM differs between simulation and hardware reset behavior;
this is a confirmed test-coverage gap, not yet a diagnosed cause. Do not disable
video checks or relax input deadlines merely to hide the symptom.

## Quartus failures

Use `jotego/jtcore20`, read the first meaningful error in the generated `jtcore.log` and Quartus reports, and compare new warnings against the stock baseline in `RESULTS.md`. Link-clock paths must not be left unconstrained or waived without a documented CDC reason.
