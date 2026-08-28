#!/usr/bin/env bash
set -euo pipefail

mode=${1:-}
rom=${2:-}
[[ ${mode} == smoke || ${mode} == long ]] || {
    echo "usage: $0 smoke|long /absolute/path/to/ROM" >&2
    exit 2
}
[[ ${rom} == /* && -f ${rom} ]] || {
    echo "ROM must be an existing absolute file path" >&2
    exit 2
}

echo "The dual-JTBUBL ${mode} harness is staged but requires ROM inspection first." >&2
echo "ROM accepted at ${rom}; no ROM data was copied into Git." >&2
exit 3
