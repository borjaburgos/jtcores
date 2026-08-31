#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

docker run --rm \
    -v "${repo_root}:/jtcores" \
    -w /jtcores \
    jotego/linter -lc \
    'set -e
     git config --global --add safe.directory /jtcores
     export JTROOT=/jtcores JTFRAME=/jtcores/modules/jtframe
     source /jtcores/modules/jtframe/bin/setprj.sh >/dev/null
     for role in HOST JOIN; do
         echo "Link2P lint: ${role}"
         /jtcores/modules/jtframe/bin/lint-one.sh bubl -pocket --nodbg \
             -d JTFRAME_LINK2P -d "JTFRAME_LINK2P_${role}"
     done'
