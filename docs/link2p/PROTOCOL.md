# Link2P protocol

## Version 1 goals

The protocol is intentionally small and point-to-point. It performs compatibility checks, coordinates startup, transports one local player's frame-associated controls in each direction, and exchanges diagnostics.

Host is the only SCK source. Both endpoints drive SO and sample SI. Bits are transferred most-significant first in fixed-size full-duplex slots. Packets are rejected unless their magic, protocol version, and CRC are valid.

## Packet fields

Version 1 is a 192-bit, MSB-first packet:

```text
[191:176] magic 0x4c32 ("L2")
[175:168] protocol version 1
[167]     role (1 Host, 0 Join)
[166:164] message (WAIT/HELLO/ARMED/GO/RUN/FAULT)
[163:160] local protocol state
[159:144] session ID
[143:136] packet sequence
[135:120] target logical frame
[119:108] local active-low joystick/start/coin sample
[107:92]  DIP tag
[91:60]   build ID 0x4c325001
[59:52]   game ID 0x42
[51:20]   previous completed-frame video CRC-32
[19:8]    sender logical-frame low bits
[7:0]     CRC-8
```

CRC-8 uses polynomial `0x07`, initial value `0x00`, over every packet bit except the transmitted CRC byte.

At the hardware defaults, 48 MHz `clk48` and a half divider of 24 produce a
1 MHz cable clock. A 192-bit transfer takes 192 microseconds and is followed by
a four-microsecond low-SCK framing gap. Join oversamples SCK/SI through explicit
synchronizers; Host synchronizes SI. CRC is accumulated one bit per received
edge so no packet-wide combinational CRC path exists.

## Messages and startup

```text
WAIT_FOR_PEER -> HELLO -> ARMED -> BOUNDARY -> GO -> PENDING -> RUNNING
                                                              \-> FAULT
FAULT -> RECOVER/WAIT -> fresh HELLO session
```

Host creates the session ID and repeatedly advertises HELLO. Join accepts only an opposite role with matching version, build, game, and DIP values, then echoes ARMED with the Host session. Host sends GO; both endpoints arm reset release. Each endpoint removes its link reset hold on the next synchronized Pocket `vblank` edge, allowing the existing JTFRAME reset path to complete.

During recovery, both roles advertise WAIT before beginning a fresh session.
Cable contacts may reconnect at different times, so a recovering Join also
accepts a valid fresh Host HELLO. This prevents a Host that received WAIT
first from stranding the Join in RECOVER.

Packets from another session, duplicate/stale sequences, out-of-window frames,
bad CRCs, incompatible builds/DIPs, peer faults, or peer timeout cannot update
game inputs. Duplicate and stale sequence flags latch for diagnostics. A
four-entry frame-keyed buffer detects overwrite/overflow; entries are cleared
when consumed. Missing data at its required boundary faults instead of reusing
the prior sample.

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

Named, preserved target nets expose link enable, configured role, peer presence,
session establishment, session ID, TX/RX sequence, last valid frame, CRC error,
stale/duplicate packet, role conflict, timeout, buffer overflow, desync, CRC
error count, and timeout count for the status grid or SignalTap.
