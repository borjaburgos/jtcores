#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
pocket_dir=/jtcores/modules/jtframe/target/pocket

tests=(serial protocol startup fault sequence)
for test_name in "${tests[@]}"; do
    echo "Link2P unit: ${test_name}"
    docker run --rm \
        -v "${repo_root}:/jtcores" \
        -w "${pocket_dir}" \
        jotego/linter -lc \
        "iverilog -g2012 -Wall -o /tmp/link2p-${test_name}.vvp hdl/jtframe_pocket_link_serial.v hdl/jtframe_pocket_link2p.v ver/link2p_${test_name}_tb.v && vvp /tmp/link2p-${test_name}.vvp"
done

echo "Link2P unit: JTBUBL clean restart RAM"
docker run --rm \
    -v "${repo_root}:/jtcores" \
    -w /jtcores \
    jotego/linter -lc \
    "iverilog -g2012 -Wall -o /tmp/link2p-jtbubl-reset.vvp cores/bubl/hdl/jtbubl_link2p_ram_clear.v modules/jtframe/hdl/ram/jtframe_dual_ram.v scripts/link2p/verilog/jtbubl_reset_tb.v && vvp /tmp/link2p-jtbubl-reset.vvp"

echo "Link2P unit suite: PASS"
