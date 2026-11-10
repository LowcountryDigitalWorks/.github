"""Deterministic local contract for the pinned Betterleaks download.

This does not download Betterleaks, scan a repository, or call GitHub.
"""

from __future__ import annotations

import hashlib
import http.server
import shutil
import subprocess
import tarfile
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-secrets.yml"
SHA256SUM = Path(r"C:\Program Files\Git\usr\bin\sha256sum.exe")
CURL = shutil.which("curl") or shutil.which("curl.exe")

VERSION = "1.7.4"
SHA256 = "9ed7739a39a26a2217f38726bff8a8f4fe079d3b21272caa7959823ccc444d96"
ASSET_URL = (
    "https://github.com/betterleaks/betterleaks/releases/download/"
    "v${BETTERLEAKS_VERSION}/betterleaks_${BETTERLEAKS_VERSION}_linux_x64.tar.gz"
)
RETRY_FLAGS = [
    "--retry",
    "3",
    "--retry-delay",
    "2",
    "--retry-max-time",
    "45",
    "--connect-timeout",
    "10",
    "--max-time",
    "20",
]


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self.server.hits += 1
        mode = self.server.mode
        if mode == "always504" or (mode == "twice504" and self.server.hits <= 2):
            body = b"gateway timeout"
            status = 504
        elif mode == "missing":
            body = b"missing"
            status = 404
        else:
            body = self.server.payload
            status = 200
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def install_step(text: str) -> str:
    start = text.index("      - name: Install verified Betterleaks\n")
    end = text.index("      - name: Verify detector with runtime-only canary\n")
    return text[start:end]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check_workflow() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").replace("\r\n", "\n")
    step = install_step(text)
    assert_true(f'BETTERLEAKS_VERSION: "{VERSION}"' in text, "version pin changed")
    assert_true(f'BETTERLEAKS_SHA256: "{SHA256}"' in text, "sha256 pin changed")
    assert_true(ASSET_URL in step, "asset URL changed")
    assert_true("--proto '=https'" in step, "HTTPS protocol lock missing")
    assert_true("--tlsv1.2" in step, "TLS 1.2 floor missing")
    assert_true("--retry-all-errors" not in step, "retry-all-errors widens the failure set")
    assert_true("--retry-connrefused" not in step, "connection-refused retry was not requested")
    assert_true("continue-on-error" not in text, "continue-on-error weakens the mandatory step")
    assert_true("|| true" not in step, "a swallowed curl failure is not fail-closed")
    collapsed = " ".join(step.replace("\\", " ").split())
    expected = " ".join(RETRY_FLAGS)
    assert_true(expected in collapsed, f"retry flags are not exactly {expected}")
    checksum_at = step.index("sha256sum --check --strict")
    tar_at = step.index("tar -xzf")
    assert_true(checksum_at < tar_at, "checksum does not run before tar")
    assert_true(step.index("curl") < checksum_at, "checksum does not follow the download")
    assert_true("permissions:\n  contents: read\n" in text, "permissions changed")
    for name in (
        "Materialize immutable trusted Betterleaks config",
        "Enforce sanitized Betterleaks configuration environment",
        "Install LDW Betterleaks invocation wrapper",
        "Verify detector with runtime-only canary",
        "Verify caller Betterleaks config cannot weaken trusted policy",
        "Verify title-only caller betterleaks.toml cannot weaken trusted policy",
        "Verify inline allow signatures cannot suppress trusted detections",
        "Verify BETTERLEAKS_CONFIG_TOML injection cannot weaken trusted policy",
        "Verify Git-history scope and fail-closed revision resolution",
        "Verify scan mode binding refuses workflow_run and unknown events",
        "Bind caller-authoritative scan mode",
        "Resolve caller-authoritative Git scan scope",
        "Scan caller-authoritative Git history without exposing findings",
        "Scan caller candidate tree for merge/reconciliation results",
    ):
        assert_true(f"- name: {name}\n" in text, f"downstream step missing: {name}")
    assert_true("--ignore-gitleaks-allow" in text, "inline allow rejection missing")
    assert_true('LDW_BETTERLEAKS' in text, "wrapper missing")
    assert_true("scan_is_pull_request:" in text, "workflow_call scan authority missing")


def serve(mode: str, payload: bytes) -> tuple[http.server.HTTPServer, int]:
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    server.mode = mode
    server.hits = 0
    server.payload = payload
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def curl_to(url: str, dest: Path, https_only: bool = False) -> subprocess.CompletedProcess[str]:
    command = [CURL, "--fail", "--location", "--silent", "--show-error"]
    if https_only:
        command.extend(["--proto", "=https", "--tlsv1.2"])
    else:
        command.extend(RETRY_FLAGS)
    command.extend(["--output", str(dest), url])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def checksum(expected: str, archive: Path) -> subprocess.CompletedProcess[str]:
    listing = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="\n")
    listing.write(f"{expected}  {archive}\n")
    listing.close()
    try:
        return subprocess.run(
            [str(SHA256SUM), "--check", "--strict", listing.name],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(listing.name).unlink(missing_ok=True)


def fixture_archive() -> bytes:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        payload = root / "marker.txt"
        payload.write_text("ldw-retry-fixture\n", encoding="utf-8")
        archive_path = root / "fixture.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(payload, arcname="marker.txt")
        return archive_path.read_bytes()


def check_behavior() -> None:
    assert_true(CURL is not None, "curl is not on PATH")
    assert_true(SHA256SUM.exists(), "sha256sum is not available")
    payload = fixture_archive()
    digest = hashlib.sha256(payload).hexdigest()

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        server, port = serve("always504", payload)
        try:
            failed = curl_to(f"http://127.0.0.1:{port}/asset", root / "failed.tar.gz")
            assert_true(failed.returncode != 0, "persistent HTTP 504 must fail the download")
            assert_true(server.hits == 4, f"expected 4 attempts, saw {server.hits}")
            assert_true(not (root / "extracted").exists(), "failure path extracted an archive")
        finally:
            server.shutdown()

        server, port = serve("missing", payload)
        try:
            missing = curl_to(f"http://127.0.0.1:{port}/asset", root / "missing.tar.gz")
            assert_true(missing.returncode != 0, "HTTP 404 must fail")
            assert_true(server.hits == 1, f"HTTP 404 was retried {server.hits} times")
        finally:
            server.shutdown()

        server, port = serve("bad200", b"not-the-pinned-archive")
        try:
            downloaded = curl_to(f"http://127.0.0.1:{port}/asset", root / "bad.tar.gz")
            assert_true(downloaded.returncode == 0, "HTTP 200 download should reach checksum")
            assert_true(server.hits == 1, "checksum mismatch must not be retried as HTTP 5xx")
            checked = checksum(digest, root / "bad.tar.gz")
            assert_true(checked.returncode != 0, "checksum mismatch must fail")
            assert_true(not (root / "extracted").exists(), "checksum mismatch extracted an archive")
        finally:
            server.shutdown()

        server, port = serve("twice504", payload)
        try:
            archive = root / "good.tar.gz"
            downloaded = curl_to(f"http://127.0.0.1:{port}/asset", archive)
            assert_true(downloaded.returncode == 0, "transient HTTP 504 then success should download")
            assert_true(server.hits == 3, f"expected 3 attempts, saw {server.hits}")
            checked = checksum(digest, archive)
            assert_true(checked.returncode == 0, "matching checksum must pass before extraction")
            extracted = root / "extracted"
            extracted.mkdir()
            with tarfile.open(archive, "r:gz") as opened:
                opened.extractall(extracted)
            assert_true((extracted / "marker.txt").is_file(), "expected fixture was not extracted")
        finally:
            server.shutdown()

        server, port = serve("bad200", payload)
        try:
            rejected = curl_to(
                f"http://127.0.0.1:{port}/asset",
                root / "plain.tar.gz",
                https_only=True,
            )
            assert_true(rejected.returncode != 0, "plain HTTP must fail the HTTPS-only curl flags")
            assert_true(server.hits == 0, "HTTPS-only curl contacted a plain HTTP server")
        finally:
            server.shutdown()


def main() -> None:
    check_workflow()
    check_behavior()
    print("betterleaks_install_retry=PASS")


if __name__ == "__main__":
    main()
