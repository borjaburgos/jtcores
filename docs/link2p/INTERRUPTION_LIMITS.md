# Interruption limit characterization

This measures the protocol-2 / `0x4c325003` candidate at 250 kHz. It does not
change the production RTL, extend the input deadline, or implement pause.
The tested HDL is the same as the `49991da` hardware bundle.

## Results — 2026-09-15

**Longest demonstrated recovery: 48.25 ms.** The next tested duration,
48.50 ms, failed in that same favorable configuration. This is a sampled
boundary at 0.25 ms resolution, not an absolute maximum over all timing.

**14.00 ms passed all 80 timing/wire combinations.** The most sensitive
combination failed at 14.25 ms. Do not present the best-case 48.25 ms as a
general disconnect allowance.

| Peer frame offset | Range of per-scenario longest passes in the fixed-phase matrix |
| --- | --- |
| 317 clocks (~6.6 microseconds) | 31.00–47.25 ms |
| 405,474 clocks (half a frame) | 23.75–36.50 ms |
| 809,948 clocks (almost a frame) | 14.00–30.50 ms |

The main sweep completed 1,514 trials (913 passed, 601 stopped on a missing
input deadline). The 14 ms common-duration cross-check passed every scenario;
no sampled shorter failure preceded a longer success in the same scenario.
Another 218 trials deliberately interrupted immediately after both peers
accepted fresh inputs, covering 16 packet alignments. These established the
48.25/48.50 ms best-case bracket. No successful trial reset or changed session,
and no trial triggered the wrong-input scoreboard.

The best case used all contacts interrupted, a 317-clock peer offset, and a
24,192-clock startup shift. The interruption began 56,742 clocks into the
frame (1.182125 ms). Both peers recovered an input from history. The most
sensitive case used all contacts interrupted, an 809,948-clock peer offset,
a 24,192-clock startup shift, and an interruption starting at frame phase
48,000 (1 ms).

The existing tolerance regression also passed unchanged: 23 short-outage
cases, every packet bit corrupted in both directions, and safe sustained-loss
reset. Production RTL and the existing hardware bundle were not modified.

Private evidence is under `JTBUBL-Link2P/interruption-20260915` in the artifact
root: `summary.json`, `results.csv`, `trials/`, `fresh-start.log`,
`fresh-phase-sweep.log`, `zero-controls.log`, and `tolerance-regression.log`.
Source hashes distinguish the original sweep binary from the final testbench.
The original nominal-zero controls toggled the contacts for one clock due to
edge scheduling; all 80 were repeated successfully with the corrected true
zero-interruption control. Nonzero trial timing was unaffected.

## Method

`make link2p-interruption OUT=/absolute/path/to/new-results` builds the
ROM-free real-wire testbench in the existing `jotego/linter` image. Allow
several minutes; the runner uses up to 12 independent simulation processes.
The output directory contains source hashes, compiler output, a log per trial,
`results.csv`, and `summary.json`. Existing result CSVs are not overwritten.

Each trial establishes a fresh session, runs six warm-up frames, interrupts
selected contacts, and observes four complete frames after restoring them.
Both endpoints run the actual CRC publisher, serial receiver, input history,
and deadline logic. Every applied P1/P2 sample, including Coin and Start,
must match an independent changing-input scoreboard. Resetting either peer
or changing session is failure, not recovery. Unexpected failures abort the
experiment instead of being classified as a duration limit.

The frame period is 810,948 clocks at nominal 48 MHz (16.89475 ms). The matrix
contains 80 combinations:

- Eight interruption start phases across the frame, including just before
  and after input sampling.
- Peer frame offsets of 317, 405,474, and 809,948 clocks.
- Near-aligned peers: all contacts interrupted together, either data
  direction alone, and the clock held low or high.
- Large peer offsets: all contacts interrupted together.
- All three peer offsets also repeat the all-contact test with game startup
  shifted by half a serial slot (24,192 clocks), changing packet alignment.

An 8 ms coarse grid covers 0–56 ms. Each scenario's largest passing region is
then scanned in 1 ms and 0.25 ms steps. This is not binary search: the runner
reports shorter failing samples if they exist. Finally, every scenario is
tested at the smallest of the measured per-scenario maxima. This last
cross-check must pass before calling that duration common to the matrix.

For the additional favorable-timing scan, the compiled testbench accepts
`+fresh_start` with `+start_phase=0 +peer_phase=317`. It waits until both peers
have accepted their newest remote input before opening the contacts. For
example, after the standard runner builds the executable:

```bash
for offset in {0..45360..3024}; do
    for duration_us in {47000..50000..250}; do
        /absolute/path/to/new-results/bin/Vlink2p_interruption_tb \
            +fresh_start +start_phase=0 +peer_phase=317 +direction=0 \
            +warm_offset="$offset" +duration_clks="$((duration_us*48))"
    done
done
```

The private supplementary logs also include 46–46.75 and 50.25 ms samples
at startup offsets 0 and 24,192 clocks. The command above reproduces the
best-case bracket at all 16 alignments without those redundant outer points.

## Interpretation

The longest passing trial is a best-case observation, not a guaranteed
disconnect allowance. Frame phase, packet phase, which contact breaks, and
which inputs already arrived all affect the deadline. The two-sample history
can repair losses only while the required input remains available and can
arrive before use. It cannot restore an already-diverged game.

This finite grid does not prove all intermediate durations or phases, other
frame rates, independent oscillator drift, repeated contact bounce, or real
Pocket gameplay. Frame fingerprints in this test are synthetic and correctly
labelled; this is not the earlier dual-game simulation or a hidden-state
equivalence test. A later physical playtest must measure actual fault counters.
