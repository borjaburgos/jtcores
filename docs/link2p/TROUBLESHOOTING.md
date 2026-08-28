# Link2P troubleshooting

## Session never leaves WAIT_FOR_PEER

- Confirm one Host and one Join package are running.
- Confirm the GB/GBC cable is fully seated and compatible.
- Check SCK activity from Host and confirm Join leaves SCK high impedance.
- Inspect peer timeout and CRC counters.
- Two Join packages are indistinguishable from a disconnected cable and intentionally remain waiting.

## ROLE CONFLICT or BUILD/DIP mismatch

- Verify package role and RBF SHA-256.
- Verify protocol/build IDs and source commits in the manifest.
- Verify identical DIP settings.
- Power/reset both sessions and retry with a fresh session ID.

## Input mismatch

- Confirm final controls are active low.
- Confirm Pocket's local controller is the source presented as JTFRAME player 1 before Link2P remapping.
- Check target logical frame, sequence, and both buffered player samples.
- Never bypass the frame buffer for local input.

## DESYNC

Record the first logical frame and both fingerprints. Check, in order: ROM/DIP/build identity, reset release diagnostics, input frame/sequence, packet CRC/stale counters, uninitialized RAM, then MCU-visible state. Do not modify JTBUBL before target-level causes are disproven.

## Quartus failures

Use `jotego/jtcore20`, read the first meaningful error in the generated `jtcore.log` and Quartus reports, and compare new warnings against the stock baseline in `RESULTS.md`. Link-clock paths must not be left unconstrained or waived without a documented CDC reason.
