#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
if [[ $# != 1 ]]; then
    echo "Usage: bash scripts/link2p/run-interruption.sh OUTPUT_DIRECTORY" >&2
    exit 2
fi
mkdir -p "$1"
output_dir=$(cd "$1" && pwd)
if [[ -e "$output_dir/results.csv" ]]; then
    echo "Refusing to overwrite an existing interruption sweep: $output_dir" >&2
    exit 2
fi
{
    git -C "$repo_root" rev-parse HEAD
    git -C "$repo_root/modules/jtframe/target/pocket" rev-parse HEAD
    git -C "$repo_root" status --short
    git -C "$repo_root/modules/jtframe/target/pocket" status --short
    cd "$repo_root"
    sha256sum modules/jtframe/target/pocket/hdl/jtframe{,_pocket}_link2p.v \
        modules/jtframe/target/pocket/hdl/jtframe_pocket_link_serial.v \
        modules/jtframe/target/pocket/ver/link2p_{interruption,tolerance}_tb.sv \
        scripts/link2p/interruption-sweep.py
} > "$output_dir/SOURCE.txt"
docker run --rm --user "$(id -u):$(id -g)" \
    -v "$repo_root:/jtcores:ro" -v "$output_dir:/out" \
    -w /jtcores/modules/jtframe/target/pocket jotego/linter -lc '
    set -e
    verilator --binary --timing -j 4 -Wno-fatal --top-module link2p_interruption_tb \
        --Mdir /out/bin hdl/jtframe_pocket_link_serial.v hdl/jtframe_link2p.v \
        hdl/jtframe_pocket_link2p.v ver/link2p_tolerance_tb.sv \
        ver/link2p_interruption_tb.sv > /out/build.log 2>&1 ||
        { cat /out/build.log; exit 1; }
    python3 /jtcores/scripts/link2p/interruption-sweep.py \
        --binary /out/bin/Vlink2p_interruption_tb --out /out
    ' | tee "$output_dir/sweep.log"
