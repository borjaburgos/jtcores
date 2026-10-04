#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sim_dir=$(mktemp -d /tmp/link-serial.XXXXXXXX)
trap 'rm -rf -- "$sim_dir"' EXIT
for crc_bits in 8 32; do
    if [[ ${SIM:-iverilog} == verilator ]]; then
        verilator --binary --timing -j 4 -Wno-fatal --top-module test \
            -GCRC_BITS="$crc_bits" -GHALF_DIV="${HALF_DIV:-96}" \
            -GJOIN_HALF_NS="${JOIN_HALF_NS:-10.418}" --Mdir "$sim_dir/obj" \
            ../../hdl/jtframe_pocket_link_serial.v test.sv > "$sim_dir/build.log" 2>&1 ||
            { cat "$sim_dir/build.log"; exit 1; }
        "$sim_dir/obj/Vtest"
    elif [[ ${SIM:-iverilog} == iverilog ]]; then
        iverilog -g2012 -Wall -s test -Ptest.CRC_BITS="$crc_bits" \
            -Ptest.HALF_DIV="${HALF_DIV:-8}" -Ptest.JOIN_HALF_NS="${JOIN_HALF_NS:-10.418}" \
            -o "$sim_dir/test" ../../hdl/jtframe_pocket_link_serial.v test.sv
        vvp "$sim_dir/test"
    else
        echo 'SIM must be iverilog or verilator' >&2
        exit 2
    fi
    iverilog -g2012 -Wall -s link2p_crc_tb -Plink2p_crc_tb.CRC_BITS="$crc_bits" \
        -o "$sim_dir/crc" ../../hdl/jtframe_pocket_link_serial.v crc_test.sv
    vvp "$sim_dir/crc"
done
