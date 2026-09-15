# Link2P protocol

## Version 2

Two complete local games exchange frame-associated digital controls, startup
coordination, and diagnostics. No game state, video, or audio is sent. The
session module is transport-independent; the Pocket adapter uses a GB/GBC
cable with Host-generated SCK and full-duplex SO/SI.

Version 2 repeats the newest and previous input samples, labels video CRCs by
their own frame, and uses a stronger packet checksum. It is incompatible with
version 1; update both endpoints together.

## Packet layout

248 bits, MSB first:

```text
[247:232] magic 0x4c32 ("L2")
[231:224] protocol version 2
[223]     role (1 Host, 0 Join)
[222:220] message (WAIT/HELLO/ARMED/GO/RUN/FAULT)
[219:216] local protocol state
[215:200] session ID
[199:192] packet sequence
[191:176] newest input target frame
[175:164] newest input (12 active-low bits)
[163:148] DIP tag
[147:116] build ID (current candidate: 0x4c325003)
[115:108] core-defined game ID (JTBUBL: 0x42)
[107:76]  completed-frame video CRC-32
[75:64]   sender logical-frame low bits (diagnostic)
[63:48]   video CRC logical frame
[47:36]   previous input (target = newest target - 1)
[35]      previous input valid
[34]      newest input valid
[33]      video CRC valid
[32]      reserved, zero
[31:0]    packet CRC-32/MPEG-2
```

Packet CRC uses polynomial `0x04c11db7`, initial value `0xffffffff`, no
reflection and no final XOR, over bits `[247:32]`. It is distinct from the
video fingerprint. A CRC is error detection, not authentication or a proof
against every possible corruption.

48 MHz `clk48` and a half divider of 96 produce 250 kHz SCK. A transfer takes
992 microseconds, followed by a 16-microsecond low-SCK framing gap: about 16.8
slots per 59.19 Hz frame. Join detects a gap after eight microseconds low,
four normal half-bit intervals. SCK/SI pass through explicit synchronizers.
Receive CRC accumulates per bit; transmit CRC is calculated before the slot
snapshot. Both role builds must pass timing analysis.

## Startup and recovery

```text
WAIT -> HELLO -> ARMED -> BOUNDARY -> GO -> PENDING -> RUNNING
                                                       | fault
                                                       v
                         fresh HELLO <- RECOVER <- FAULT
```

Host chooses a session ID. Join accepts an opposite role with matching
version, build, game ID, and DIP tag, then echoes ARMED with that session.
Host starts GO just after a local diagnostic-video boundary. Both peers arm
reset release for their next local diagnostic-video boundary and let the
existing JTFRAME reset path complete. There is no global shared clock or
claim of arbitrary phase/drift tolerance.

Faulted peers hold game reset, spend a quiet recovery interval advertising
FAULT, then advertise WAIT. Host starts a new session. A recovering Join also
accepts a fresh compatible HELLO, so contacts reconnecting at different times
do not strand it in RECOVER. Long interruptions discard game progress and
retain the clean reset-to-NOTICE behavior.

Two Join builds safely wait without SCK. Two Host builds are an invalid
electrical configuration; do not deliberately connect two SCK drivers.

## Input deadline and retransmission

The sample is `{Coin, Start, joystick[9:0]}`, all active low. At logical frame
N each peer captures its local controls for target N+2. The four-slot buffer
is keyed by the full 16-bit target frame. At the application boundary, both
games receive the Host sample as P1 and the Join sample as P2. The initial two
frames use neutral input; no uncaptured sample is advertised as valid.

Every RUN packet repeats the newest capture and, once available, its
predecessor. Losing the original one-frame transmission window no longer
necessarily loses that input: history can still arrive before its deadline.
Retransmissions are idempotent. Consumed history is discarded; conflicting
values for an outstanding frame, a future target outside the buffer window,
or an alias of another pending frame fault the session. Sequence arithmetic
and frame arithmetic are modular; tests cover their wrap boundaries.

Bad-checksum packets are discarded. They neither update inputs nor keep a
dead peer alive. Duplicate/stale sequences cannot update inputs. There is no
per-input ACK, prediction, stale-input substitution, pause, or rollback.
If either required sample is absent at its application boundary, reset is
asserted. Therefore tolerance is bounded by input timing, peer phase, and
time to receive a complete clean packet—not a universal disconnect duration.

## Video check and diagnostics

The session captures a stable synchronized video CRC eight `clk48` cycles
after the game blanking marker. Its tag names that completed logical frame,
independently of the input target. After five warm-up frames, only matching
CRC frame tags authorize comparison. A genuine same-frame mismatch faults;
different-frame fingerprints are not compared. CRC agreement checks visible
output, not all hidden game state.

Preserved target nets expose enable, role, peer/session status, session ID,
TX/RX sequence, last valid input frame, CRC/stale/duplicate flags, role
conflict, timeout, overflow, and video desync. Saturating 16-bit counters
record damaged slots, timeouts, inputs recovered from history, and missed
input deadlines. `last_fault_code` survives automatic reconnection, unlike
the current fault band. These clear on FPGA/PLL reset, not a session restart.

Fault codes: 1 role, 2 identity, 3 peer/session, 4 peer timeout, 5 input, 6 video.
For code 5, an increased deadline counter distinguishes missing input from
conflicting input or a buffer-window violation. The peer may report code 3
after receiving the originating side's fault; record both screens.
