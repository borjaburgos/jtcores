#!/usr/bin/env python3
"""Characterize sampled interruption limits; no monotonicity assumption.

Runs the compiled real-wire testbench, not game/ROM simulation. Each trial
starts a fresh session and either checks four frames after restoring the wire
or records the first reset. A reset is a measurement, a scoreboard failure is
a failed experiment. Results are local evidence, not a hardware guarantee.
"""

import argparse
import concurrent.futures
import csv
import json
from pathlib import Path
import re
import subprocess

FRAME_CLKS = 810948
CLOCKS_PER_MS = 48000
SCENARIO_FIELDS = ("start_phase", "peer_phase", "direction", "warm_offset")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=12)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("jobs must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    logs = args.out / "trials"
    logs.mkdir(exist_ok=True)
    results = []
    completed = set()
    writer = None

    def run(job):
        scenario, duration = job
        values = dict(zip(SCENARIO_FIELDS, scenario))
        values["duration_clks"] = duration
        command = [str(args.binary.resolve())]
        command += [f"+{key}={value}" for key, value in values.items()]
        name = "-".join(str(value) for value in (*scenario, duration))
        process = subprocess.run(command, capture_output=True, text=True, timeout=180)
        output = process.stdout + process.stderr
        (logs / f"{name}.log").write_text(output)
        matches = re.findall(r"^RESULT (.*)$", output, flags=re.MULTILINE)
        if process.returncode or len(matches) != 1:
            raise RuntimeError(f"Invalid trial {name}: see {logs / (name + '.log')}")
        row = dict((key, int(value)) for key, value in
                   (field.split("=") for field in matches[0].split()))
        if any(row.get(key) != value for key, value in values.items()):
            raise RuntimeError(f"Trial metadata mismatch: {name}")
        # Only the deliberately exhausted input deadline is expected here.
        # Identity/CRC-state/video failures must not masquerade as a limit.
        if not row["recovered"] and not (
            (row["fault_h"] == 5 and row["missed_h"] > 0) or
            (row["fault_j"] == 5 and row["missed_j"] > 0)
        ):
            raise RuntimeError(f"Unexpected failure mechanism: {row}")
        return row

    with (args.out / "results.csv").open("x", newline="") as csv_file:
        def batch(name, jobs):
            nonlocal writer
            jobs = list(dict.fromkeys(job for job in jobs if job not in completed))
            print(f"{name}: {len(jobs)} independent trials", flush=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
                for index, row in enumerate(pool.map(run, jobs), 1):
                    if writer is None:
                        writer = csv.DictWriter(csv_file, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    csv_file.flush()
                    results.append(row)
                    completed.add((tuple(row[key] for key in SCENARIO_FIELDS),
                                   row["duration_clks"]))
                    if index % 40 == 0 or index == len(jobs):
                        print(f"{name}: {index}/{len(jobs)} ({len(results)} total)", flush=True)

        phases = (0, 48000, 96000, FRAME_CLKS//4, FRAME_CLKS//2,
                  3*FRAME_CLKS//4, FRAME_CLKS-48000, FRAME_CLKS-1000)
        scenarios = []
        for peer in (317, FRAME_CLKS//2, FRAME_CLKS-1000):
            for phase in phases:
                # All wire modes for near-aligned peers; all-wire outages for
                # large peer offsets and a half-slot shift of serial alignment.
                for direction in (range(5) if peer == 317 else (0,)):
                    scenarios.append((phase, peer, direction, 0))
                scenarios.append((phase, peer, 0, 24192))

        def bounds(scenario):
            rows = [row for row in results if
                    tuple(row[key] for key in SCENARIO_FIELDS) == scenario]
            passed = [row["duration_clks"] for row in rows if row["recovered"]]
            if not passed:
                raise RuntimeError(f"No passing baseline for {scenario}")
            lower = max(passed)
            failed_above = [row["duration_clks"] for row in rows if
                            not row["recovered"] and row["duration_clks"] > lower]
            if not failed_above:
                raise RuntimeError(f"Sweep ceiling insufficient for {scenario}")
            return lower, min(failed_above)

        batch("coarse 8 ms grid", ((scenario, ms*CLOCKS_PER_MS)
              for scenario in scenarios for ms in range(0, 57, 8)))
        if any(not row["recovered"] for row in results if row["duration_clks"] == 0):
            raise RuntimeError("A no-interruption baseline failed")

        refinements = []
        for scenario in scenarios:
            lower, upper = bounds(scenario)
            refinements += [(scenario, duration) for duration in
                            range(lower+CLOCKS_PER_MS, upper, CLOCKS_PER_MS)]
        batch("1 ms refinement", refinements)

        # Refine every bracket rather than assuming the current best/worst
        # case stays the extreme after increasing measurement resolution.
        refinements = []
        for scenario in scenarios:
            lower, upper = bounds(scenario)
            refinements += [(scenario, duration) for duration in
                            range(lower+12000, upper, 12000)]
        batch("0.25 ms refinement", refinements)

        common = min(bounds(scenario)[0] for scenario in scenarios)
        batch("common-duration cross-check", ((scenario, common) for scenario in scenarios))
        common_passed = all(row["recovered"] for row in results
                            if row["duration_clks"] == common)
        summary = {
            "frame_clks": FRAME_CLKS,
            "clock_hz": 48000000,
            "trials": len(results),
            "scenarios": len(scenarios),
            "common_duration_clks": common,
            "common_duration_all_passed": common_passed,
            "boundaries": [],
        }
        for scenario in scenarios:
            lower, upper = bounds(scenario)
            row = dict(zip(SCENARIO_FIELDS, scenario))
            row.update(longest_pass_clks=lower, next_fail_clks=upper)
            # Report holes instead of hiding them behind a threshold claim.
            row["shorter_failures"] = sorted(result["duration_clks"] for result in results
                if tuple(result[key] for key in SCENARIO_FIELDS) == scenario
                and not result["recovered"] and result["duration_clks"] < lower)
            summary["boundaries"].append(row)
        (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
