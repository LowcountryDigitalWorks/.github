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
        "ldw_quarantine_candidate_fingerprint_ignore_policies",
        "ldw_scan_quarantined_policy_blobs",
        "ldw_vault_git_policy_blobs_at_ref",
        "LDW_POLICY_BLOB_VAULT",
        "candidate-policy-bytes.dat",
        "Verify candidate fingerprint-ignore files cannot suppress trusted detections",
        "fingerprint-ignore symlinks are refused",
        "Vault attestation must inspect unchanged policy blob bytes",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"missing fingerprint-ignore control: {needle}")
    if "ldw_vault_git_policy_blobs_at_ref" not in text or "ldw_scan_quarantined_policy_blobs" not in text:
        raise SystemExit("production scans must attest and vault-scan policy blobs")
    if "ldw_quarantine_candidate_fingerprint_ignore_policies ." not in text:
        raise SystemExit("git production scan must quarantine candidate ignore policies")
    if 'ldw_quarantine_candidate_fingerprint_ignore_policies "$scan_dir"' not in text:
        raise SystemExit("dir/merge-tree production scan must quarantine candidate ignore policies")
    print("secret_scan_fingerprint_ignore_contract=PASS")


if __name__ == "__main__":
    main()
