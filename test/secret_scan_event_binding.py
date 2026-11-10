"""Execute bind scan mode selftest (not substring-only contract checks)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELFTEST = ROOT / "test" / "bind_scan_mode_logic.sh"


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


def main() -> None:
    if not SELFTEST.is_file():
        raise SystemExit("bind_scan_mode_logic.sh missing")
    proc = subprocess.run(
        [bash_executable(), str(SELFTEST), "selftest"],
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
