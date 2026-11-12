#!/usr/bin/env bash
# Offline mirror of workflow ldw_list_policy_vault_slots for hostile enumeration tests.
set -euo pipefail

vault="${1:?vault required}"
list_file="${2:?list file required}"
find_status=0

: >"$list_file"
set +e
if [[ -n "${LDW_TEST_FIND_SCRIPT:-}" ]]; then
  bash "$LDW_TEST_FIND_SCRIPT" "$vault" -mindepth 1 -maxdepth 1 -type d -print0 >"$list_file"
else
  find "$vault" -mindepth 1 -maxdepth 1 -type d -print0 >"$list_file"
fi
find_status=$?
set -e

if [[ "$find_status" -ne 0 ]]; then
  rm -f "$list_file"
  echo 'Policy-blob vault enumeration failed (fail-closed).' >&2
  exit "$find_status"
fi

exit 0
