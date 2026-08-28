#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "usage: $0 host|join [diagnostic]" >&2
    exit 2
}

role=${1:-}
mode=${2:-normal}
[[ ${role} == host || ${role} == join ]] || usage
[[ ${mode} == normal || ${mode} == diagnostic ]] || usage

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
artifact_root=${PRIVATE_ARTIFACT_ROOT:-}
[[ ${artifact_root} == /* ]] || {
    echo "PRIVATE_ARTIFACT_ROOT must be an absolute path" >&2
    exit 2
}

role_macro=JTFRAME_LINK2P_HOST
[[ ${role} == join ]] && role_macro=JTFRAME_LINK2P_JOIN
diag_arg=
[[ ${mode} == diagnostic ]] && diag_arg='-d JTFRAME_LINK2P_DIAGNOSTIC'

docker run --rm --network host \
    -v "${repo_root}:/jtcores" \
    jotego/jtcore20 -lc \
    "cd /jtcores && export JTROOT=/jtcores JTFRAME=/jtcores/modules/jtframe JTUTIL=/jtutil PATH=\$PATH:/usr/local/go/bin && git config --global --add safe.directory /jtcores && source /jtcores/modules/jtframe/bin/setprj.sh >/dev/null && mkdir -p /jtutil && printf 00000000 | xxd -r -p > /jtutil/beta.bin && jtframe mra --nodbg --skipROM bubl && jtutil seed --max-trials 4 bubl -pocket --nodbg --nolinter -d JTFRAME_LINK2P -d ${role_macro} ${diag_arg}"

source_dir=${repo_root}/release/pocket/raw
destination=${artifact_root}/JTBUBL-Link2P/work/${mode}/${role}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
if [[ -d ${destination} ]]; then
    backup=${destination}.backup-${timestamp}
    echo "Preserve previous role build: ${destination} -> ${backup}"
    mv "${destination}" "${backup}"
fi
mkdir -p "${destination}/quartus-reports"
cp -a "${source_dir}" "${destination}/core-package"
cp -a \
    "${repo_root}"/cores/bubl/seed/pocket/0/build/jtbubl.{asm,eda,fit,flow,map,sta}.rpt \
    "${repo_root}"/cores/bubl/seed/pocket/0/build/jtbubl.{fit,map,sta}.summary \
    "${repo_root}"/cores/bubl/seed/pocket/0/jtcore.log \
    "${destination}/quartus-reports/"
super_commit=$(git -C "${repo_root}" rev-parse HEAD)
pocket_commit=$(git -C "${repo_root}/modules/jtframe/target/pocket" rev-parse HEAD)
printf '%s\n' \
    '{' \
    "  \"jtcores_commit\": \"${super_commit}\"," \
    "  \"pocket_commit\": \"${pocket_commit}\"," \
    "  \"role\": \"${role}\"," \
    "  \"mode\": \"${mode}\"" \
    '}' > "${destination}/source-manifest.json"
echo "Preserved ${role}/${mode} build at ${destination}"
