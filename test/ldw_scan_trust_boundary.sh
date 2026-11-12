#!/usr/bin/env bash
# Offline reference for LDW scan trust boundary (workflow materializes matching logic to RUNNER_TEMP).
set -euo pipefail

ldw_policy_blob_vault() {
  local vault="${LDW_POLICY_BLOB_VAULT:-$RUNNER_TEMP/ldw-policy-blob-vault}"
  mkdir -p "$vault"
  printf '%s' "$vault"
}

ldw_quarantine_policy_bytes() {
  local logical_path="$1"
  local origin_kind="$2"
  local bytes_file="$3"
  local vault digest slot
  vault="$(ldw_policy_blob_vault)"
  digest="$(sha256sum <"$bytes_file" | awk '{print $1}')"
  slot="$vault/$digest"
  if [[ ! -f "$slot/candidate-policy-bytes.dat" ]]; then
    mkdir -p "$slot"
    cp -- "$bytes_file" "$slot/candidate-policy-bytes.dat"
    printf '%s\n' "$logical_path" >"$slot/origin.logical.path"
    printf '%s\n' "$origin_kind" >"$slot/origin.kind"
  fi
}

ldw_quarantine_candidate_fingerprint_ignore_policies() {
  local root="${1:?scan root required}"
  local name path tmp
  for name in .betterleaksignore .gitleaksignore; do
    path="${root%/}/${name}"
    if [[ -L "$path" ]]; then
      echo 'Candidate fingerprint-ignore symlinks are refused (fail-closed).' >&2
      return 1
    fi
    if [[ ! -e "$path" ]]; then
      continue
    fi
    if [[ ! -f "$path" ]]; then
      echo 'Candidate fingerprint-ignore must be a regular file (fail-closed).' >&2
      return 1
    fi
    tmp="$(mktemp)"
    cp -- "$path" "$tmp"
    ldw_quarantine_policy_bytes "${root}/${name}" working-tree "$tmp"
    rm -f "$tmp" "$path"
  done
}

if [[ "${1:-}" == 'neutralize-selftest' ]]; then
  export LDW_POLICY_BLOB_VAULT="$(mktemp -d)"
  work="$(mktemp -d)"
  trap 'rm -rf "$work" "$LDW_POLICY_BLOB_VAULT"' EXIT
  printf 'policy-bytes\n' >"$work/.gitleaksignore"
  ldw_quarantine_candidate_fingerprint_ignore_policies "$work"
  test ! -f "$work/.gitleaksignore"
  test -f "$LDW_POLICY_BLOB_VAULT"/*/candidate-policy-bytes.dat
  touch "$work/symlink-target"
  ln -s "$work/symlink-target" "$work/.gitleaksignore"
  if ldw_quarantine_candidate_fingerprint_ignore_policies "$work" 2>/dev/null; then
    echo 'expected symlink refusal' >&2
    exit 1
  fi
  echo 'ldw_scan_trust_boundary_selftest=PASS'
fi
