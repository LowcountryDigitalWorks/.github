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

Existing repository-specific secret controls remain in place until each product workstream deliberately adopts and validates the reusable baseline. Callers should reference an independently reviewed immutable commit SHA of this repository rather than `@main` or another mutable reference.

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
