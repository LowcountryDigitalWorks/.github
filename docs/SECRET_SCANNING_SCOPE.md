# Reusable secret-scanning scope

Status: candidate under issue #18 until independently reviewed and merged.

## Purpose

LDW's reusable Betterleaks control must catch secrets in authoritative repository history without allowing an unrelated abandoned feature branch to block every future pull request.

Betterleaks' default `git` history mode traverses full history across all refs when no custom Git log scope is supplied. GitHub Actions full-depth checkout can make multiple remote branch refs available locally. Therefore `betterleaks git .` without a scope is broader than the caller's authoritative change boundary.

The reusable workflow keeps full-depth checkout for commit-object availability but passes an explicit Betterleaks `--log-opts` scope.

## Pull requests

For `pull_request` and `pull_request_target` callers, the workflow uses the exact caller event SHAs:

```text
<github.event.pull_request.base.sha>..<github.event.pull_request.head.sha>
```

This scans commits reachable from the candidate head that are not reachable from the PR base. The workflow fails closed if either SHA is missing or unavailable locally.

The scan is keyed to immutable event SHAs rather than mutable branch names. An unrelated remote branch may exist in the checkout, but it is not part of the Betterleaks candidate range and cannot independently fail that PR.

A later force-push/synchronize event supplies a new exact head SHA and therefore creates a new candidate history scope.

## Push, manual, and other non-PR callers

For non-PR callers, the workflow scopes Betterleaks to:

```text
<github.sha>
```

`git log <sha>` traverses the complete history reachable from that authoritative caller commit. This preserves the intended full accepted-history check for `main`/default-branch runs without adding unrelated side branches through `--all`.

## Security properties preserved

The correction does **not** change:

- Betterleaks v1.7.4;
- the pinned upstream archive digest;
- `permissions: contents: read`;
- `persist-credentials: false`;
- 100% finding redaction;
- generic-only CI failure messages;
- no report/artifact upload;
- 10-minute timeout;
- runtime detector canary.

The self-test additionally creates a temporary Git repository and proves all three behaviors:

1. a detector-shaped runtime canary committed only on an unrelated branch does not fail a safe selected candidate range;
2. the same canary committed inside the selected PR-style candidate range is detected;
3. a non-PR scan rooted at the selected head detects the canary in that head's reachable history.

The temporary repository and scanner logs are deleted. Canary contents are constructed only at runtime and are never committed to the LDW repository.

## Why this is not a weakening

The pull-request gate exists to evaluate the candidate being proposed for acceptance. Side branches that are not part of that candidate are not authoritative inputs to that decision.

When a candidate is merged, the main-push scan checks the complete history reachable from the resulting authoritative main SHA. Thus a secret introduced by an accepted PR remains detectable on the authoritative branch as well as before merge.

This change does not create an allowlist and does not suppress a finding in the selected history. It changes only the Git history boundary from implicit `--all` to an explicit caller-authoritative range.

## Rollout

Caller repositories pin reusable workflows to independently reviewed immutable commits of `LowcountryDigitalWorks/.github`. After this change is accepted, caller repositories must repin in separate bounded PRs before they receive the new scope semantics.

Do not delete or rewrite unrelated historical branches merely to make the central scan green. Branch cleanup is a separate repository-maintenance/destructive-change decision.
