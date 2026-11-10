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
    assert_true("--config \"$BETTERLEAKS_TRUSTED_CONFIG\"" in text, "trusted --config not on all scans")
    assert_true("Bind caller-authoritative scan mode" in text, "scan mode binding missing")
    assert_true("Verify caller Betterleaks config cannot weaken trusted policy" in text, "config adversarial canary missing")
    assert_true("git merge-tree --write-tree" in text, "merge-tree coverage missing")
    assert_true("SCAN_MODE" in text, "SCAN_MODE env missing")
    assert_true("filter = \"true\"" in text, "synthetic adversarial allow filter missing")
    assert_true("continue-on-error" not in text, "continue-on-error weakens mandatory scan")
    assert_true("|| true" not in text, "swallowed failure forbidden")
    print("secret_scan_equivalence_contract=PASS")


if __name__ == "__main__":
    main()
