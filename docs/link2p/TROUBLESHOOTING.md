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

- Confirm both role manifests report build ID `0x4c325002` and
  `serial_clock_hz` 250000. Do not mix either role with a 1 MHz build.
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

Cable removal intentionally stops both games and selects the diagnostic
screen. The corrected normal build negotiates a fresh session after reconnect,
clears Link2P-visible JTBUBL work and MCU communication RAM while reset is
held, and returns both systems to a clean NOTICE screen. Credits plus Start
must begin a new game without exiting either core. This deliberately discards
the interrupted game; seamless preservation or resumption of live-game state
is outside the POC scope.

If Start loops back to NOTICE, first verify corrected normal bitstreams (Host
SHA-256 `03fc0edf0f6082e3f31901968c3638a4eaae7679ee1f0fdbeef104ddec026fd3`,
Join SHA-256 `bbb0bf74c7cb53c00b9de7665e9afba390b9ea6232c9e9b590cb78f38abf947b`).
Exit and relaunch Join followed by Host only as a fallback, and preserve the
build manifests plus the first visible diagnostic state for investigation.

## Quartus failures

Use `jotego/jtcore20`, read the first meaningful error in the generated `jtcore.log` and Quartus reports, and compare new warnings against the stock baseline in `RESULTS.md`. Link-clock paths must not be left unconstrained or waived without a documented CDC reason.
