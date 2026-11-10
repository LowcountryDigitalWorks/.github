# Reusable secret-scanning scope

Status: BO #552 hosted-equivalence repair candidate (**SOURCE_ONLY / UNACCEPTED** until author-excluded H0/M0).

## Purpose

The reusable Betterleaks control scans both the caller-authoritative commit history and the candidate's current tree. History scanning preserves detection for secrets added and later removed, while the tree scan covers merge or conflict-resolution content that exists in the candidate result without appearing in the exact PR-head history.

The workflow keeps a full-depth checkout so exact event commits are available. Betterleaks remains pinned to v1.7.4 and its verified archive checksum.

## Pull requests

For pull_request and pull_request_target callers, the history scan uses the immutable event base and head SHAs, plus Betterleaks v1.7.4's existing diff filter:

    betterleaks git . --log-opts="<base-sha>..<head-sha> --diff-filter=tuxdb"

The workflow requires both revisions to be 40-character commit SHAs and to resolve locally as commits. Missing, malformed, branch-name, or unavailable revisions fail closed. Fork heads that are not available in the checkout also fail closed.

The exact SHA range selects commits reachable from the candidate head that are not reachable from the PR base. An unrelated remote branch is outside this history range. For every pull-request-shaped scan (including `workflow_call` with `scan_is_pull_request: true` and exact base/head inputs), the workflow resolves `git merge-tree --write-tree` from exact base/head commit objects, materializes a read-only worktree with `git read-tree` and `git checkout-index` (no `git archive`, no hooks), and scans that tree with Betterleaks `dir` through a workflow-owned invocation wrapper. The wrapper always passes explicit `--config` with `[extend] useDefault = true`, unsets `BETTERLEAKS_CONFIG` / `BETTERLEAKS_CONFIG_TOML` (and legacy `GITLEAKS_*` aliases), and passes Betterleaks v1.7.4 `--ignore-gitleaks-allow` so inline allow markers cannot suppress findings. Caller-authored `betterleaks.toml`, `.betterleaks.toml`, title-only configs, and env-injected TOML cannot weaken detection. `pull_request_target` is explicitly refused. If the merge result cannot be resolved, the workflow fails closed. No candidate code is executed.

## Required-check provenance (out of scope for this repository)

This shared workflow does **not** by itself prevent a consumer repository from spoofing or no-oping a mandatory check name on `pull_request`. A PR-editable caller workflow that runs on `pull_request` can still replace the job definition under the same check label until a **separate**, trusted-main-bound caller and check-attestation design (for example `workflow_run` with immutable workflow ref and independently reviewed scope) is accepted. Consumer migration from isolated to GitHub-hosted execution is **not** security-equivalent until that provenance HIGH is closed in `business-operations` (or equivalent consumer), then repinned to an accepted immutable `.github` commit. Do not treat this source candidate alone as permission to flip `use_isolated_runner` or relax branch protection.

## Push, manual, and other non-PR callers

The history scan is rooted at the exact caller SHA and preserves the v1.7.4 diff filter:

    betterleaks git . --log-opts="<github.sha> --diff-filter=tuxdb"

The resolver rejects missing, malformed, branch-name, or unavailable caller revisions. The current-tree scan complements history scanning and does not change the authoritative history root.

## Validation canaries

When verify_canary is enabled, the workflow creates a temporary Git repository and runtime-only detector-shaped values. It proves:

1. A value on an unrelated branch does not affect a safe candidate history range.
2. A value introduced and later removed in candidate history is still detected.
3. The resolver accepts valid exact commit SHAs with the expected options and rejects blank, malformed, unavailable, and branch-name revisions.
4. A value added only while resolving a synthetic merge conflict is absent from the exact candidate head tree and detected in the merge-result tree scan materialized via `read-tree` / `checkout-index`.
5. Title-only `betterleaks.toml`, inline `betterleaks:allow` markers, and `BETTERLEAKS_CONFIG_TOML` injection do not weaken trusted detection.

The runtime and history scan output is redirected to temporary logs, logs are deleted, finding contents are never printed, and no artifact is uploaded. Canary content is not committed to Lowcountry Digital Works repositories.

## Preserved security properties

This correction preserves:

- Betterleaks v1.7.4 and the pinned upstream archive digest;
- permissions: contents: read;
- persist-credentials: false;
- full-depth checkout for commit-object availability;
- 100% finding redaction and generic CI failure messages;
- no report artifact, new credential, permission, customer data, or paid service;
- exact PR base/head SHAs and non-PR history rooted at exact github.sha.

The history boundary changes only which commits Betterleaks traverses. The v1.7.4 --diff-filter=tuxdb behavior remains explicit. The additional current-tree pass covers merge/reconciliation results that are not represented by the PR head's commit range.

## Rollout

Caller repositories pin reusable workflows independently to immutable commits. Any caller repinning is a separate, bounded change after the shared workflow correction is accepted. Do not delete or rewrite historical branches to make the central scan pass.
