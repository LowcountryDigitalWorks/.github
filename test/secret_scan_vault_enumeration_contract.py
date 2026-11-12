"""Fail-closed contract for policy-vault slot enumeration (M1)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-secrets.yml"
ENUM_SNIPPET = ROOT / "test" / "ldw_list_policy_vault_slots.sh"
FAKE_FIND = ROOT / "test" / "fixtures" / "find_exit_73.sh"


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").replace("\r\n", "\n")
    if re.search(r"done\s*<\s*<\(\s*find\s+\"\$vault\"", text):
        raise SystemExit("vault enumeration must not use unchecked find process substitution")
    if "ldw_list_policy_vault_slots" not in text:
        raise SystemExit("trusted vault list helper missing")
    if "Policy-blob vault enumeration failed (fail-closed)" not in text:
        raise SystemExit("enumeration failure message missing")
    if "find_status" not in text:
        raise SystemExit("find exit status must be checked explicitly")

    if not ENUM_SNIPPET.is_file():
        raise SystemExit("enumeration snippet runner missing")
    if not FAKE_FIND.is_file():
        raise SystemExit("find exit 73 fixture missing")

    bash_candidates = [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
    ]
    bash = next((str(p) for p in bash_candidates if p.is_file()), None) or shutil.which("bash")
    if bash is None:
        raise SystemExit("bash unavailable for enumeration fail-closed regression")

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        list_file = Path(tmp) / "slots.null"
        env = {
            **os.environ,
            "LDW_TEST_FIND_SCRIPT": str(FAKE_FIND.resolve()),
        }
        proc = subprocess.run(
            [str(bash), str(ENUM_SNIPPET), str(vault), str(list_file)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if proc.returncode != 73:
            raise SystemExit(f"expected fail-closed exit 73, got {proc.returncode}")
        if list_file.exists() and list_file.stat().st_size > 0:
            raise SystemExit("partial enumeration output must not persist after find failure")

    print("secret_scan_vault_enumeration_contract=PASS")


if __name__ == "__main__":
    main()
