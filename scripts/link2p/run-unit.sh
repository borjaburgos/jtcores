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

echo "Link2P unit suite: PASS"
