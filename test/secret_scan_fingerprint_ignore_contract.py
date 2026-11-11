"""Contract checks for fingerprint-ignore fail-closed treatment in security-secrets.yml."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-secrets.yml"


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").replace("\r\n", "\n")
    required = [
        "BETTERLEAKS_TRUSTED_EMPTY_IGNORE",
        "ldw-trusted-empty.betterleaksignore",
        "--gitleaks-ignore-path",
        "LDW_SCAN_TRUST_BOUNDARY",
        "ldw_neutralize_candidate_fingerprint_ignores",
        "Verify candidate fingerprint-ignore files cannot suppress trusted detections",
        "fingerprint-ignore symlinks are refused",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"missing fingerprint-ignore control: {needle}")
    if "ldw_neutralize_candidate_fingerprint_ignores ." not in text:
        raise SystemExit("git production scan must neutralize candidate ignore files")
    if 'ldw_neutralize_candidate_fingerprint_ignores "$scan_dir"' not in text:
        raise SystemExit("dir/merge-tree production scan must neutralize candidate ignore files")
    print("secret_scan_fingerprint_ignore_contract=PASS")


if __name__ == "__main__":
    main()
