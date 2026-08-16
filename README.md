# Lowcountry Digital Works Organization Standards

This repository is the GitHub organization control plane for Lowcountry Digital Works (LDW). It provides shared GitHub-facing standards and orchestration that should be reusable across LDW repositories without forcing application projects to duplicate organization-wide workflow logic.

## Responsibilities

This repository owns or may own, as those capabilities are adopted and validated:

- the public GitHub organization profile and community-health files;
- contribution, security, support, and governance standards;
- issue and pull-request templates;
- starter workflow templates for new repositories;
- organization-wide reusable GitHub Actions workflows;
- thin orchestration of reusable development and repository-security tooling;
- common GitHub Actions supply-chain standards; and
- documentation for how LDW repositories consume shared workflows.

Application repositories should eventually consume proven reusable workflows from this repository instead of independently duplicating organization-wide scanners and workflow logic. Reusable workflows should be referenced by reviewed immutable commit SHA rather than mutable references such as `@main`. External GitHub Actions used by LDW workflows should likewise use reviewed full commit SHAs wherever practical.

## Current validation baseline

This repository self-validates its GitHub workflow definitions and starter workflow templates with deterministic open-source tools in GitHub Actions:

- **actionlint v1.7.12** for GitHub Actions syntax and semantic validation; and
- **zizmor v1.29.0** for static analysis of GitHub Actions security posture.

The workflow downloads the official Linux release binaries directly from their upstream GitHub releases, verifies pinned SHA-256 digests before execution, and runs zizmor in offline mode. No wrapper Action, hosted scanner account, local workstation installation, or recurring subscription is required for this baseline.

## Reusable secret-scanning baseline

`security-secrets.yml` provides the first reusable LDW repository-security workflow. It uses **Betterleaks v1.7.4**, downloaded from its immutable upstream GitHub release and verified against a pinned SHA-256 digest before execution. The workflow checks out the caller repository with full history, uses read-only GitHub permissions, and suppresses potential secret contents from CI output and artifacts.

`prove-secret-scanning.yml` is a thin self-test for that reusable workflow. It enables a runtime-only synthetic canary so changes to the central implementation must demonstrate that the detector still finds a known test pattern before the control repository accepts them.

The reusable secret workflow has been cross-repository validated from the private `LowcountryDigitalWorks/business-operations` repository. Existing repository-specific secret controls remain in place until each product workstream deliberately adopts and validates the reusable baseline. Callers should reference an independently reviewed immutable commit SHA of this repository rather than `@main` or another mutable reference.

## Reusable JavaScript dependency-scanning baseline

`security-dependencies-npm.yml` provides the reusable LDW dependency-vulnerability workflow for JavaScript lockfiles using **OSV-Scanner v2.5.0**. The initial scope is intentionally limited to the lockfiles OSV-Scanner documents for JavaScript: `bun.lock`, `package-lock.json`, `pnpm-lock.yaml`, and `yarn.lock`. Other ecosystems should be added only when an LDW repository actually requires them and their privacy/cost behavior has been separately validated.

The reusable workflow downloads the official Linux amd64 OSV-Scanner release artifact and verifies SHA-256 `edcfc41d257db36148f065055655fe3fcfc434b0b423ea67468a84c207524e0c` before execution. Scanner stdout and stderr are redirected to ephemeral runner files that are deleted without being emitted or uploaded; CI exposes only fixed, sanitized messages and process status. Existing ecosystem-native audits such as npm/pnpm audit remain independent controls.

### Privacy model

The workflow's default is privacy-preserving offline matching. Callers must explicitly set `online_queries: true` to permit OSV network queries using caller dependency metadata.

In default offline mode, the workflow downloads and verifies OSV-Scanner, then bootstraps the npm vulnerability database against a runtime-only synthetic public lockfile **before the caller repository is checked out**. Dependency resolution is disabled during bootstrap. Only after the local database and detector are verified does the workflow check out the caller repository and inspect its JavaScript lockfiles using full `--offline` mode with `--no-resolve`.

This ordering means private/customer dependency files are not present on the runner during the OSV database-bootstrap network phase. Online mode is an explicit opt-in intended primarily for public repositories; private/customer exceptions require a deliberate repository-owner/workstream decision.

For OSV-Scanner v2.5.0, LDW uses the source-defined `--local-db-path` option to bind the local vulnerability database to an explicit ephemeral runner path. The documented environment/cache-location mechanisms did not direct the database to the expected path in the tested `scan source` flow. Because this option is hidden upstream, OSV-Scanner is pinned and the workflow is self-tested; any scanner upgrade must revalidate this behavior.

The accepted GitHub-hosted Ubuntu offline proof measured an npm vulnerability-database footprint of **219,428,884 bytes (about 209 MiB)**, a **13-second** database bootstrap, and an **11-second** cached fully offline canary scan. These are point-in-time measurements, not performance guarantees. Cache/freshness optimization remains deferred until repeated caller usage makes it worthwhile.

### Self-tests and rollout

`prove-dependency-scanning.yml` is a thin self-test of the reusable workflow's explicit online path using a runtime-only vulnerable npm canary. `prove-osv-offline-mode.yml` is a thin self-test of the default offline path; offline bootstrap inherently verifies the same vulnerable canary before scanning the control repository.

The reusable workflow was first adopted by the public `LowcountryDigitalWorks/secure-exchange` application repository through PR #17. That caller references the independently reviewed central commit `ebf64d4e7fb2bb6bab287601bb516612768a6a20`, explicitly opts into online queries because the repository and its dependency metadata are public, and leaves the repository's existing CI and native dependency checks independent.

Full offline mode has known coverage tradeoffs, including no commit-level vulnerability matching and possible differences where network-backed dependency resolution would otherwise be used. Those tradeoffs are accepted for the privacy-preserving default and can be reconsidered per repository when justified.

## Cross-repository CI adoption governance

The Developer Tooling & CI Orchestrator may independently review and merge a narrow additive CI/governance caller change into an LDW product repository without separate Product Orchestrator concurrence when all of the following remain true:

- the change consumes an already proven central workflow or control pinned to an independently reviewed immutable commit SHA;
- the product-repository change is limited to additive workflow/governance glue and does not alter product code, dependencies, runtime behavior, architecture, provider choices, deployment assumptions, or authorized release scope;
- the change does not add, remove, rename, weaken, or otherwise alter the semantics of product-required checks, branch/release gates, or product-specific security/privacy invariants;
- permissions remain least-privilege and the caller introduces no new secret, customer-data, PHI, or consequential external-service flow unless separately approved;
- live base, exact candidate head/tree, changed files, existing product CI, the new central check, and review-thread state are independently verified before merge; and
- repository-local governance does not impose a stricter concurrence requirement.

Product Orchestrator concurrence is required before merge whenever a proposed adoption changes product-required checks or release sequencing, product architecture or runtime/deployment assumptions, dependencies, product-specific security/privacy invariants, or repository governance. A narrow direct merge under Developer Tooling & CI authority should still be followed by a concise informational handoff to the affected Product Orchestrator so product state remains current.

This rule governs only reusable CI/control adoption. It does not transfer product release, architecture, runtime, deployment, or customer-data authority to the Developer Tooling & CI workstream.

## Boundaries

This repository does **not** own:

- application-specific build, test, or release logic;
- application-specific unit, integration, or browser tests;
- website-specific SEO, crawling, or website-quality tooling;
- a copied collection of third-party scanner binaries; or
- speculative LDW custom tooling that has not yet justified its own maintained software project.

If LDW later develops enough shared executable code—such as result-normalization utilities, policy evaluators, or similar common tooling—to justify a separate general-purpose developer-tooling repository, that decision should be made explicitly rather than pre-creating one now.

Reusable website-specific quality capabilities belong in [`LowcountryDigitalWorks/website-quality-toolkit`](https://github.com/LowcountryDigitalWorks/website-quality-toolkit), whose architecture is governed separately by the LDW SEO / website-quality workstream.

## Security and privacy

This repository must not contain passwords, tokens, private keys, recovery information, client confidential information, billing records, or internal-only operating procedures.
