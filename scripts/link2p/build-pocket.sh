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

super_dirty=$(git -C "${repo_root}" status --porcelain --untracked-files=no)
pocket_dirty=$(git -C "${repo_root}/modules/jtframe/target/pocket" \
    status --porcelain --untracked-files=no)
if [[ -n ${super_dirty} || -n ${pocket_dirty} ]]; then
    echo "Refusing to build from a dirty superproject or Pocket worktree" >&2
    exit 2
fi
expected_pocket_commit=$(git -C "${repo_root}" \
    ls-tree HEAD modules/jtframe/target/pocket | awk '{print $3}')
actual_pocket_commit=$(git -C "${repo_root}/modules/jtframe/target/pocket" rev-parse HEAD)
[[ -n ${expected_pocket_commit} && ${actual_pocket_commit} == "${expected_pocket_commit}" ]] || {
    echo "Pocket checkout does not match the commit pinned by the superproject" >&2
    exit 2
}

role_macro=JTFRAME_LINK2P_HOST
[[ ${role} == join ]] && role_macro=JTFRAME_LINK2P_JOIN
diag_arg=
[[ ${mode} == diagnostic ]] && diag_arg='-d JTFRAME_LINK2P_DIAGNOSTIC'

docker run --rm --network host \
    -v "${repo_root}:/jtcores" \
    jotego/jtcore20 -lc \
    "cd /jtcores &&
     export JTROOT=/jtcores JTFRAME=/jtcores/modules/jtframe JTUTIL=/jtutil PATH=\$PATH:/usr/local/go/bin &&
     git config --global --add safe.directory /jtcores &&
     source /jtcores/modules/jtframe/bin/setprj.sh >/dev/null &&
     mkdir -p /jtutil &&
     printf 00000000 | xxd -r -p > /jtutil/beta.bin &&
     jtframe mra --nodbg --skipROM bubl &&
     jtutil seed --max-trials 4 bubl -pocket --nodbg --nolinter \
       -d JTFRAME_LINK2P -d ${role_macro} ${diag_arg}"

source_dir=${repo_root}/release/pocket/raw
release_rbf=${source_dir}/Cores/jotego.jtbubl/jtbubl.rbf_r
seed_root=${repo_root}/cores/bubl/seed/pocket
matched_seeds=()
shopt -s nullglob
for candidate in "${seed_root}"/[0-9]*/build/jtbubl.rbf_r; do
    if cmp -s "${release_rbf}" "${candidate}"; then
        relative=${candidate#"${seed_root}"/}
        matched_seeds+=("${relative%%/*}")
    fi
done
shopt -u nullglob
[[ ${#matched_seeds[@]} -eq 1 ]] || {
    echo "Expected exactly one Quartus seed to match the released bitstream; found ${#matched_seeds[@]}" >&2
    exit 1
}
seed=${matched_seeds[0]}
seed_dir=${seed_root}/${seed}
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
    "${seed_dir}"/build/jtbubl.{asm,eda,fit,flow,map,sta}.rpt \
    "${seed_dir}"/build/jtbubl.{fit,map,sta}.summary \
    "${seed_dir}"/jtcore.log \
    "${destination}/quartus-reports/"
super_commit=$(git -C "${repo_root}" rev-parse HEAD)
pocket_commit=$(git -C "${repo_root}/modules/jtframe/target/pocket" rev-parse HEAD)
printf '%s\n' \
    '{' \
    "  \"jtcores_commit\": \"${super_commit}\"," \
    "  \"pocket_commit\": \"${pocket_commit}\"," \
    "  \"role\": \"${role}\"," \
    "  \"mode\": \"${mode}\"," \
    "  \"seed\": ${seed}" \
    '}' > "${destination}/source-manifest.json"
echo "Preserved ${role}/${mode} build at ${destination}"
