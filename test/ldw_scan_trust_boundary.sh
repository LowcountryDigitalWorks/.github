#!/usr/bin/env bash
# Offline reference for LDW scan trust boundary (workflow materializes matching logic to RUNNER_TEMP).
set -euo pipefail

ldw_neutralize_candidate_fingerprint_ignores() {
  local root="${1:?scan root required}"
  local name path
  for name in .betterleaksignore .gitleaksignore; do
    path="${root%/}/${name}"
    if [[ -L "$path" ]]; then
      echo 'Candidate fingerprint-ignore symlinks are refused (fail-closed).' >&2
      return 1
    fi
    if [[ -f "$path" ]]; then
      rm -f "$path"
    fi
  done
}

if [[ "${1:-}" == 'neutralize-selftest' ]]; then
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  printf 'ignore\n' >"$work/.gitleaksignore"
  ldw_neutralize_candidate_fingerprint_ignores "$work"
  test ! -f "$work/.gitleaksignore"
  printf 'x\n' >"$work/.betterleaksignore"
  ldw_neutralize_candidate_fingerprint_ignores "$work"
  test ! -f "$work/.betterleaksignore"
  printf 'y\n' >"$work/.gitleaksignore"
  ln -sf "$work/.gitleaksignore" "$work/.gitleaksignore"
  if ldw_neutralize_candidate_fingerprint_ignores "$work" 2>/dev/null; then
    echo 'expected symlink refusal' >&2
    exit 1
  fi
  echo 'ldw_scan_trust_boundary_selftest=PASS'
fi
