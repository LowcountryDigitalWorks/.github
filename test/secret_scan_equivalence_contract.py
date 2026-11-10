"""Deterministic workflow contract checks for BO #552 hosted equivalence repair."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-secrets.yml"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert_true("permissions:\n  contents: read\n" in text, "contents:read lock missing")
    assert_true("on:\n  workflow_call:" in text or "workflow_call:" in text.split("jobs:")[0], "workflow_call reusable surface required")
    assert_true("secrets:" not in text, "secrets elevation forbidden")
    assert_true("id-token: write" not in text, "id-token write forbidden")
    assert_true("scan_is_pull_request:" in text, "workflow_call PR authority input missing")
    assert_true("scan_base_sha:" in text, "workflow_call base sha input missing")
    assert_true("scan_head_sha:" in text, "workflow_call head sha input missing")
    assert_true("Materialize immutable trusted Betterleaks config" in text, "trusted config step missing")
    assert_true('BETTERLEAKS_TRUSTED_CONFIG' in text, "trusted config env missing")
    assert_true("useDefault = true" in text, "trusted config must inherit embedded defaults")
    assert_true('title = "LDW trusted scanner policy"' in text, "trusted titled config missing")
    assert_true("Enforce sanitized Betterleaks configuration environment" in text, "env sanitization missing")
    assert_true("Install LDW Betterleaks invocation wrapper" in text, "invocation wrapper missing")
    assert_true("--ignore-gitleaks-allow" in text, "inline allow rejection missing")
    assert_true('LDW_BETTERLEAKS' in text, "wrapper invocation env missing")
    assert_true("Bind caller-authoritative scan mode" in text, "scan mode binding missing")
    assert_true("Verify caller Betterleaks config cannot weaken trusted policy" in text, "config adversarial canary missing")
    assert_true("Verify title-only caller betterleaks.toml cannot weaken trusted policy" in text, "title-only config canary missing")
    assert_true("Verify inline allow signatures cannot suppress trusted detections" in text, "inline allow canary missing")
    assert_true("Verify BETTERLEAKS_CONFIG_TOML injection cannot weaken trusted policy" in text, "env config canary missing")
    assert_true("git merge-tree --write-tree" in text, "merge-tree coverage missing")
    assert_true("git read-tree" in text, "read-tree materialization missing")
    assert_true("git checkout-index" in text, "checkout-index materialization missing")
    assert_true("pull_request_target is explicitly refused" in text, "pull_request_target refusal missing")
    assert_true("workflow_run is unsupported for mandatory secret scan invocation" in text, "workflow_run refusal missing")
    assert_true("Unsupported github.event_name for secret scan" in text, "unknown event fail-closed missing")
    assert_true("Verify scan mode binding refuses workflow_run and unknown events" in text, "event binding selftest step missing")
    assert_true("SCAN_MODE" in text, "SCAN_MODE env missing")
    assert_true("filter = \"true\"" in text, "synthetic adversarial allow filter missing")
    assert_true("betterleaks:allow" in text, "inline allow adversarial fixture missing")
    assert_true("continue-on-error" not in text, "continue-on-error weakens mandatory scan")
    assert_true("|| true" not in text, "swallowed failure forbidden")
    assert_true("git archive" not in text, "git archive merge materialization forbidden")
    print("secret_scan_equivalence_contract=PASS")


if __name__ == "__main__":
    main()
