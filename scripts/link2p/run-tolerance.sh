#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
docker run --rm -v "${repo_root}:/jtcores:ro" \
    -w /jtcores/modules/jtframe/target/pocket jotego/linter -lc '
    set -e
    for profile in 810948:317 800000:300000 960000:450000 810948:809948; do
        frame_clks=${profile%:*}
        frame_phase=${profile#*:}
        echo "Link2P tolerance: frame_clks=$frame_clks phase=$frame_phase"
        verilator --binary --timing -j 4 -Wno-fatal --top-module link2p_tolerance_tb \
            -GFRAME_CLKS=$frame_clks -GFRAME_PHASE=$frame_phase \
            --Mdir /tmp/link2p-$frame_clks-$frame_phase \
            hdl/jtframe_pocket_link_serial.v hdl/jtframe_link2p.v \
            hdl/jtframe_pocket_link2p.v ver/link2p_tolerance_tb.sv \
            >/tmp/build.log 2>&1 || { cat /tmp/build.log; exit 1; }
        /tmp/link2p-$frame_clks-$frame_phase/Vlink2p_tolerance_tb
    done'
