#!/usr/bin/env bash
# Executable reference for LDW bind scan mode rules (must match security-secrets.yml Bind step).
set -euo pipefail

ldw_bind_scan_mode() {
  local event_name="$1"
  local wf_scan_is_pr="$2"
  local wf_scan_base_sha="${3:-}"
  local wf_scan_head_sha="${4:-}"

  if [[ "$event_name" == 'pull_request_target' ]]; then
    echo 'pull_request_target is explicitly refused for the LDW reusable secret scanner.' >&2
    return 1
  fi
  if [[ "$event_name" == 'workflow_run' ]]; then
    echo 'workflow_run is unsupported for mandatory secret scan invocation; failing closed.' >&2
    return 1
  fi

  case "$event_name" in
    pull_request)
      printf '%s\n' 'SCAN_MODE=pull_request'
      ;;
    push|workflow_dispatch)
      printf '%s\n' 'SCAN_MODE=single_sha'
      ;;
    workflow_call)
      if [[ "$wf_scan_is_pr" == 'true' ]]; then
        if [[ ! "$wf_scan_base_sha" =~ ^[0-9a-fA-F]{40}$ ]] || [[ ! "$wf_scan_head_sha" =~ ^[0-9a-fA-F]{40}$ ]]; then
          echo 'workflow_call pull-request scan requires exact base/head SHAs; failing closed.' >&2
          return 1
        fi
        printf '%s\n' 'SCAN_MODE=pull_request'
        printf 'SCAN_BASE_SHA=%s\n' "$wf_scan_base_sha"
        printf 'SCAN_HEAD_SHA=%s\n' "$wf_scan_head_sha"
      else
        printf '%s\n' 'SCAN_MODE=single_sha'
      fi
      ;;
    *)
      echo "Unsupported github.event_name for secret scan: ${event_name}" >&2
      return 1
      ;;
  esac
}

run_selftest() {
  local base='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
  local head='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
  local err out

  expect_fail() {
    err="$(mktemp)"
    if ldw_bind_scan_mode "$@" >"$(mktemp)" 2>"$err"; then
      rm -f "$err"
      echo "selftest expected failure for: $*" >&2
      exit 1
    fi
    rm -f "$err"
  }

  expect_ok_contains() {
    local needle="$1"
    shift
    err="$(mktemp)"
    out="$(mktemp)"
    if ! ldw_bind_scan_mode "$@" >"$out" 2>"$err"; then
      rm -f "$err" "$out"
      echo "selftest expected success for: $*" >&2
      exit 1
    fi
    if ! grep -q "$needle" <"$out"; then
      rm -f "$err" "$out"
      echo "selftest missing ${needle} for: $*" >&2
      exit 1
    fi
    rm -f "$err" "$out"
  }

  expect_fail workflow_run false '' ''
  expect_fail workflow_run true "$base" "$head"
  expect_fail schedule false '' ''
  expect_fail repository_dispatch false '' ''
  expect_fail pull_request_target false '' ''
  expect_fail workflow_call true '' "$head"
  expect_fail workflow_call true 'not-a-sha' "$head"
  expect_fail workflow_call true "$base" ''

  expect_ok_contains 'SCAN_MODE=pull_request' pull_request false '' ''
  expect_ok_contains 'SCAN_MODE=single_sha' push false '' ''
  expect_ok_contains 'SCAN_MODE=single_sha' workflow_dispatch false '' ''
  expect_ok_contains 'SCAN_MODE=single_sha' workflow_call false '' ''
  expect_ok_contains 'SCAN_MODE=pull_request' workflow_call true "$base" "$head"
  expect_ok_contains "SCAN_BASE_SHA=${base}" workflow_call true "$base" "$head"

  echo 'bind_scan_mode_logic_selftest=PASS'
}

if [[ "${1:-}" == 'selftest' ]]; then
  run_selftest
elif [[ "${1:-}" == 'bind' ]]; then
  shift
  ldw_bind_scan_mode "$@"
fi
