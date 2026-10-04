# Framed Pocket link transport

This standalone endpoint exchanges opaque packets over a GB/GBC link cable.
One Host drives SCK; the Join samples SCK and both sides drive SO, crossed to
the other side's SI. This is a custom protocol, not a GB or GBA game protocol.
Never connect two clock-driving Hosts.

The module is intentionally not wired into a core in this change. Session
negotiation, frame-associated inputs, retransmission, game pause/reset policy,
pin assignments, and timing constraints belong to subsequent integration.
Existing Pocket builds are unaffected.

## Interface

- `tx_packet` includes the checksum. The caller supplies a coherent, settled
  packet before the next slot begins; this is not a ready/valid transmit bus.
  Mid-slot updates do not alter the in-flight packet.
- `rx_valid` pulses for every completed packet, including damaged packets.
  Accept data only when `rx_valid && rx_crc_ok`. `rx_packet` is otherwise held,
  except during reset. These signals are in the endpoint's local clock domain.
- `slot_active` marks an active transfer. The low-SCK gap delimits slots and
  allows the Join to reframe after a partial transfer or independent reset.
- `sck_oe` is permanently high for Host and low for Join. It is an output-enable
  request, not a complete physical-pin configuration.

`CRC_BITS` supports 8 (polynomial 0x07, initial 0) and 32 (CRC-32/MPEG-2,
polynomial 0x04c11db7, initial 0xffffffff). Both are MSB-first, without
reflection or final XOR. The low CRC_BITS packet bits contain the checksum.
Defaults retain the original 192-bit/CRC-8 format. The current Link2P caller
explicitly selects 248 bits / CRC-32; CRC-8 is not its production checksum.
CRC-8 accepts an all-zero packet and some multi-bit corruptions. A checksum
pass alone is not proof of peer presence or packet identity; callers must
validate their own header/session fields. Use CRC-32 for the Link2P protocol.

At 48 MHz, `HALF_DIV=96` gives 250 kHz SCK. A 248-bit transfer takes 992 us,
followed by a 16 us low gap (`GAP_CYCLES=768`). `GAP_DETECT=384` is longer
than a normal half-bit and shorter than the delimiter. Tests scale the gap
and detector to eight and four half-bit periods respectively. Tested divider /
gap / detector combinations are 96/768/384, 48/384/192, 24/192/96 and the
accelerated 8/64/32. These parameters are not independently arbitrary; invalid
values are unsupported. Cable inputs cross explicit synchronizers; physical
pin directions and timing constraints are the integrating target's job.

## Tests

From the JTCORES root, with Icarus installed:

```sh
bash modules/jtframe/target/pocket/ver/link_serial/sim.sh
```

This tests both CRC widths at divider 8. For the hardware-rate matrix, also
install Verilator and run:

```sh
for divider in 96 48 24; do
    for join_half in 10.416 10.418; do
        SIM=verilator HALF_DIV=$divider JOIN_HALF_NS=$join_half \
            bash modules/jtframe/target/pocket/ver/link_serial/sim.sh
    done
done
```

Both commands also run fixed vectors under Icarus. No ROM, submodule checkout,
FPGA build, or game simulation is required. Temporary build files stay outside
the checkout and are removed on exit. The existing `jotego/linter` container
provides both simulators if they are not installed locally.

The endpoint test uses phase-offset clocks; the matrix checks Join clocks
approximately 96 ppm faster and slower than Host at 250, 500 and 1,000 kHz.
Both CRC widths check changing complete packets, mid-transfer transmit updates,
single-cycle receive strobes, held receive data, and every packet bit corrupted
in both directions. CRC-32 also checks five contact-loss modes at three packet
positions and independent mid-slot resets. Recovery waits are bounded to the
requested clean-packet count plus three slots; this is packet reframing, not
a guarantee that a game's input deadline can be met.
The fixed-vector test is independent of the endpoint test's CRC generator:
it checks a known valid checksum and explicitly demonstrates an all-zero
packet and a damaged packet tail accepted by CRC-8 but rejected by CRC-32.

Validation on 2026-10-04: Icarus 13.0 passed both accelerated configurations;
Verilator 5.050 passed all 12 hardware-rate/clock-drift/CRC combinations above.
Both roles and CRC widths also elaborate under standalone Verilator lint, with
width and unused-signal warnings in the unchanged HDL. No stock build inputs
are modified, and no new FPGA synthesis or hardware playtest is claimed here.

## Hardware context and limits

The HDL is unchanged from the Link2P candidate `49991da` (Pocket `d31d180`).
The user reports two-Pocket gameplay working while the physical link stays
intact: consoles lying flat work as expected, while active handheld play can
partially unseat a cable and interrupt the connection. This is an observed
physical connection issue, not a failure reported during stable connected play.
It is not a measured endurance or all-cables result.

The separate POC tolerates some short interruptions using input history;
sustained loss still resets the games. Recovery has sometimes looped through
NOTICE and the diagnostic screen. That post-loss integration issue remains
unresolved. Restoring the link and preserving/resuming a live game after loss
are separate follow-up goals, not features supplied by this endpoint. The
1 MHz endpoint tests likewise do not establish 1 MHz session safety: the POC's
sequence ordering imposed a separate limit during the speed experiment.
See the [full POC status](https://github.com/borjaburgos/jtcores/blob/borjaburgos/jtbubl-link2p-poc/docs/link2p/POC_STATUS.md).
This extraction adds no menu or game-core variants. A single core with an
Off / Host / Join setting is the proposed later UI, pending maintainer input.

Developed by Borja Burgos with assistance from OpenAI Codex.
