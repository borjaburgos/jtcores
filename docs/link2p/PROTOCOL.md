# Link2P protocol

## Version 1 goals

The protocol is intentionally small and point-to-point. It performs compatibility checks, coordinates startup, transports one local player's frame-associated controls in each direction, and exchanges diagnostics.

Host is the only SCK source. Both endpoints drive SO and sample SI. Bits are transferred most-significant first in fixed-size full-duplex slots. Packets are rejected unless their magic, protocol version, and CRC are valid.

## Packet fields

The initial RTL uses a fixed packet carrying:

```text
magic
protocol version
role and message type
session ID
sequence number
target logical frame
local active-low joystick/start/coin sample
DIP-switch value
build ID
game ID
previous completed-frame CRC-32
status/reserved bits
CRC-8
```

CRC-8 uses polynomial `0x07`, initial value `0x00`, over every packet bit except the transmitted CRC byte.

## Messages and startup

```text
WAIT_FOR_PEER -> HELLO -> ARMED -> GO -> RUNNING
                                      \-> LINK_ERROR / DESYNC
```

Host creates the session ID and repeatedly advertises HELLO. Join accepts only an opposite role with matching version, build, game, and DIP values, then echoes ARMED with the Host session. Host sends GO; both endpoints arm reset release. Each endpoint removes its link reset hold on the next synchronized Pocket `vblank` edge, allowing the existing JTFRAME reset path to complete.

Packets from another session, duplicate sequences, stale frames, bad CRCs, incompatible builds/DIPs, peer faults, or peer timeout cannot update game inputs.

Two Join builds cannot distinguish one another from a disconnected cable because neither drives SCK. They remain safely in WAIT_FOR_PEER and never release reset. Two Host builds can exchange enough data to report a role conflict, but SCK contention is an invalid hardware configuration and must not be used intentionally.

## Inputs

The transmitted local sample is 12 active-low bits:

```text
[9:0] joystick
[10]  Start
[11]  Coin
```

At frame N, each side samples its local source for target N+2. Both endpoints buffer samples by target frame. At the application VBL, the Host sample becomes final P1 and the Join sample becomes final P2 on both Pockets.

No stale sample is reused. A missing required sample at its application boundary enters LINK_ERROR and reasserts linked-session reset.

## Diagnostics

Each packet includes the sender's logical frame, sequence, status, and previous completed-frame video CRC. The first incompatible fingerprint for the same logical frame latches DESYNC. Recovery always creates a fresh session and starts both game instances from reset.
