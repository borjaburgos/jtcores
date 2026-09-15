# JTBUBL Link2P architecture

## Scope and invariants

The proof of concept runs one complete, independent JTBUBL instance on each Analogue Pocket. Each instance owns all writable game state and produces its own video and audio. The link cable transports only startup coordination, frame-associated inputs, and diagnostics.

Stock JTBUBL builds retain their existing logic. Link2P-specific JTBUBL changes
must be compile-time guarded and require evidence that target-only logic cannot
provide a clean, deterministic restart.

## Existing Pocket paths

### Physical link port

Stock `modules/jtframe/target/pocket/hdl/jtframe_pocket_top.v` leaves all four link-port pins in high impedance. Link2P builds enable the directions below. Pin assignments and I/O standards are in `pocket.qsf`.

The public openFPGA GBC reference establishes the direction convention used by Pocket cores:

- a direction value of `1` enables output;
- `port_tran_so` is the serial output and is driven by both peers;
- `port_tran_si` is the serial input;
- the internal-clock peer drives `port_tran_sck`, while an external-clock peer leaves it high impedance;
- `port_tran_sd` is not required for the two-peer serial link and remains high impedance.

The Link2P Host therefore drives SCK and SO. The Join drives SO, samples SCK, and leaves SCK high impedance. A normal GB/GBC link cable crosses each Pocket's SO to the other Pocket's SI.

### Controls

The control path is:

```text
Pocket bridge cont1_key
  -> jtframe_pocket_ctrlmux
  -> jtframe_pocket_joystick
  -> jtframe_board input merge/rotation/lock
  -> active-low game_joy1/game_joy2, game_start, game_coin
  -> jtframe_game_instance.v
  -> jtbubl_game
  -> jtbubl_main MCU/cabinet reads
```

Pocket `cont1_key` is active high. `jtframe_pocket_joystick` converts direction order to the JTFRAME convention (bit 0 right, bit 1 left, bit 2 down, bit 3 up, actions at bit 4 and above). `jtframe_board` presents active-low controls to game cores. JTBUBL consumes six joystick bits per player because `JTFRAME_BUTTONS=2`; Start and Coin are separate active-low vectors.

Link2P intercepts the final active-low controls in `jtframe_pocket_top.v`, after all ordinary Pocket mapping but before `jtframe_game_instance.v`. This keeps ordinary input behavior intact and ensures that both local and remote inputs pass through the same frame pipeline.

Host maps its local P1 sample to final P1 and the received Join sample to final P2. Join maps the received Host sample to final P1 and its local P1-source sample to final P2. The unused high joystick bits and player 3/4 Start/Coin remain inactive.

### Reset and VBL

The existing path is:

```text
Pocket bridge reset request / ROM load / framework reset
  -> jtframe_pocket_base.rst_req
  -> jtframe_board
  -> jtframe_reset
  -> game_rst in the clk_rom domain
  -> jtbubl_game.rst
```

`jtframe_reset` synchronizes the request across clock domains and provides a fixed release tail. The current implementation does not itself wait for a VBL edge. Link2P adds a Pocket-target-only hold request to this existing path and removes that hold only after the handshake is complete and a synchronized blanking edge from the always-running local diagnostic video timer is observed. It does not add a second game reset generator.

Game `LVBL` is used after release to number logical frames and latch frame-associated controls. The local diagnostic timer provides the startup boundary because game `LVBL` may be static while JTBUBL is held in reset and the Pocket top-level `vblank` input is Dock-driven.

## Selected POC design

- Two compile-time packages: `JTFRAME_LINK2P_HOST` and `JTFRAME_LINK2P_JOIN`.
- Fixed-size full-duplex serial slots over SO/SI.
- Host-generated 250 kHz SCK; packet layout and timing are specified in
  [PROTOCOL.md](PROTOCOL.md).
- CRC-protected packet with protocol/build/game identity, role, session,
  sequence, current and previous input samples, DIP value, status, and an
  explicitly frame-tagged video fingerprint.
- Host/Join handshake while both games remain in reset.
- Two-frame input pipeline. Inputs sampled during logical frame N target N+2.
- Damaged packets are discarded while repeated input history can still fill
  the buffer. A missing sample at its application deadline terminates the
  session; the last input is never silently reused.
- Active-video CRC-32 is exchanged as a diagnostic. A mismatch stops both sessions; CRC data is not used to repair state.
- Faulted peers enter a quiet recovery handshake, generate a new Host session
  ID, and restart both complete local game instances through the same reset path.
- A target-only status grid is visible while reset is held. A diagnostic build
  can keep it visible for cable bring-up; normal builds switch to complete local
  JTBUBL video once the session starts.
- Stock builds compile the new logic out and retain the existing high-impedance link-port behavior.

## Clock-domain approach

The serial endpoint runs in `clk48`. Host SCK is divided from that clock. Join SCK is asynchronous and is sampled through a multi-flop synchronizer before edge detection. Serial data is sampled only after the synchronized SCK edge. Completed packets and all protocol state remain in `clk48`; controls are already stable system-domain values, and frame/VBL inputs are synchronized before use.

No combinational clock gating is permitted. Host SCK is a data output generated by registered logic, not an internal gated clock.

Video CRC is a frame-stable bus, not a free-running counter. After synchronizing
the game blanking marker, the session waits eight `clk48` cycles before
capturing the synchronized CRC bus and its logical frame tag. A new target
integration must verify that settling bound for its video clock domain.

## Framework boundary

`jtframe_link2p.v` owns packet semantics, session state, frame-keyed inputs,
reset policy, and diagnostics. It has no Pocket pin or JTBUBL gameplay
dependencies. `jtframe_pocket_link2p.v` adapts it to the serial endpoint;
`jtframe_pocket_top.v` connects controls, reset, clocks, video, and status.
These modules remain in the Pocket target during the POC, ready for a later
framework move without coupling the protocol to the cable pins.

Each participating core declares `JTFRAME_LINK2P_GAME_ID`; JTBUBL uses `8'h42`.
That identity is a compatibility gate, not proof of game determinism. A new
core still needs identical ROM/settings, deterministic cold and warm reset,
compatible frame cadence, two-player digital controls, and its own gameplay
validation. Analog controls, more than two players, runtime role selection,
and arbitrary clock drift are not implemented. The guarded JTBUBL RAM scrub
remains game-specific: the protocol cannot initialize an unknown core's RAM.

## Packaging

Stock `jotego.jtbubl` remains untouched. A packaging step copies generated ROM-free files into unique private development packages:

```text
borjaburgos.JTBUBLLinkHost
borjaburgos.JTBUBLLinkJoin
```

The install helper accepts an external assembled `.rom`, verifies its hash, and copies it directly to both unique Assets trees on an SD card. ROM data never enters Git or a distributable package.

## Validation status

The accepted local ROM is identified by size and cryptographic hashes before
simulation, packaging, or installation; ROM bytes never enter Git or the
ROM-free bundle. Dual-instance simulation has matched video and audio across
three 10,000-frame input patterns and an alternate common reset timing. The
simulation's second instance shares the first instance's SDRAM response;
those results are not an independent-memory or divergent-execution proof.
See the [September review](REVIEW-20260915.md).

Two Pocket hardware testing has confirmed startup, two-player controls,
gameplay through multiple levels, and automatic recovery after cable removal.
Recovery intentionally discards the interrupted game, scrubs Link2P-visible
JTBUBL work RAM, and returns both peers to a clean NOTICE/start flow after
reconnection. The September protocol experiment extends tolerance of temporary
packet loss before the input deadline; it does not freeze or restore game
state. Its simulation results do not yet establish hardware reliability.

## Freeze-and-resume exploration

An eventual transport experiment may preserve a live game by holding both local
instances before a missing input reaches its application frame. This is a
bounded extension, not a claim that arbitrary divergent state can be repaired.
The two-frame input delay provides a candidate detection window, but simulation
must prove the bound for cable loss at every serial bit and frame phase.

The September 1 staggered `dip_pause` experiment is inconclusive: the shared
SDRAM response can supply the second instance with data for the first
instance's address once their execution diverges. The pause runner is disabled
until both controllers have independent memory models. We cannot infer either
successful state preservation or a fundamental pause limitation from that
run. Any eventual hold must preserve all state relevant to deterministic
continuation while leaving transport and status alive; it must not gate an
FPGA clock combinationally.

On reconnection, peers must exchange at least the retained session identity,
last committed logical frame, input sequence, and a state fingerprint. Resume
is allowed only after those values agree and the cable has remained healthy
for a defined stability window. Any disagreement, expired detection window, or
repeated cable chatter falls back to the existing clean reset-to-NOTICE path.
The first validation target is therefore lossless continuation from an agreed
commit boundary, not rollback or state transfer between divergent instances.
