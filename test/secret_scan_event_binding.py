"""Execute bind scan mode selftest and forbid caller-tree execution in workflow."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-secrets.yml"
OFFLINE_BINDER = ROOT / "test" / "bind_scan_mode_logic.sh"

FORBIDDEN_WORKFLOW_PATTERNS = (
    r"test/bind_scan_mode_logic",
    r"bash\s+test/",
    r"source\s+test/",
    r"\./test/bind_scan_mode_logic",
)


def bash_executable() -> str:
    if sys.platform != "win32":
        return "/bin/bash"
    for candidate in (
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
    ):
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("bash")
    if found:
        return found
    raise SystemExit("bash not found for bind scan mode selftest")


def assert_trusted_workflow_surface() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").replace("\r\n", "\n")
    for pattern in FORBIDDEN_WORKFLOW_PATTERNS:
        if re.search(pattern, text):
            raise SystemExit(f"workflow must not execute caller checkout tests: matched {pattern}")
    if "RUNNER_TEMP/ldw-bind-scan-mode.sh" not in text:
        raise SystemExit("trusted RUNNER_TEMP binder materialization missing")
    if "LDW_BIND_SCAN_MODE_TRUSTED" not in text:
        raise SystemExit("trusted binder heredoc marker missing")
    if 'LDW_BIND_SCAN_MODE" bind' not in text and "LDW_BIND_SCAN_MODE\" bind" not in text:
        if '"$LDW_BIND_SCAN_MODE" bind' not in text:
            raise SystemExit("production bind must invoke trusted RUNNER_TEMP binder")


def main() -> None:
    assert_trusted_workflow_surface()
    if not OFFLINE_BINDER.is_file():
        raise SystemExit("bind_scan_mode_logic.sh missing")
    proc = subprocess.run(
        [bash_executable(), str(OFFLINE_BINDER), "selftest"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "bind scan mode selftest failed\n")
        raise SystemExit(proc.returncode)
    if "bind_scan_mode_logic_selftest=PASS" not in proc.stdout:
        raise SystemExit("bind scan mode selftest marker missing")
    print("secret_scan_event_binding=PASS")


if __name__ == "__main__":
    main()
