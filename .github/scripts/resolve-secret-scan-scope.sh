#!/usr/bin/env bash
set -euo pipefail

event_name="${1:-}"
pr_base_sha="${2:-}"
pr_head_sha="${3:-}"
caller_sha="${4:-}"

is_available_commit() {
  local revision="$1"
  [[ "$revision" =~ ^[0-9a-fA-F]{40}$ ]] && git cat-file -e "${revision}^{commit}" 2>/dev/null
}

case "$event_name" in
  pull_request|pull_request_target)
    if ! is_available_commit "$pr_base_sha" || ! is_available_commit "$pr_head_sha"; then
      echo "Secret scan cannot resolve pull-request base/head SHAs; failing closed." >&2
      exit 1
    fi
    printf '%s..%s --diff-filter=tuxdb\n' "$pr_base_sha" "$pr_head_sha"
    ;;
  *)
    if ! is_available_commit "$caller_sha"; then
      echo "Secret scan cannot resolve caller SHA; failing closed." >&2
      exit 1
    fi
    printf '%s --diff-filter=tuxdb\n' "$caller_sha"
    ;;
esac
