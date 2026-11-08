"""Static fail-closed contract for actionlint/zizmor release downloads; no network."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validate-workflows.yml"

TOOLS = {
    "actionlint": {
        "version": 'ACTIONLINT_VERSION: "1.7.12"',
        "digest": 'ACTIONLINT_SHA256: "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"',
        "url": "https://github.com/rhysd/actionlint/releases/download/v",
    },
    "zizmor": {
        "version": 'ZIZMOR_VERSION: "1.29.0"',
        "digest": 'ZIZMOR_SHA256: "dd96df044a6e8538d5f423790f453bdd03d49e5b2bcc38214acc41a2f1297839"',
        "url": "https://github.com/zizmorcore/zizmor/releases/download/v",
    },
}

class ValidationDownloadContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = WORKFLOW.read_text(encoding="utf-8")
        cls.blocks = {}
        for name in TOOLS:
            title = "Install verified " + name
            start = cls.data.index("      - name: " + title)
            nextstep = cls.data.find("      - name:", start + 1)
            cls.blocks[name] = cls.data[start:nextstep if nextstep > 0 else None]

    def test_only_pinned_https_assets(self):
        for name, pin in TOOLS.items():
            with self.subTest(name=name):
                self.assertIn(pin["version"], self.data)
                self.assertIn(pin["digest"], self.data)
                self.assertIn(pin["url"], self.blocks[name])
                self.assertEqual(self.blocks[name].count(pin["url"]), 1)
                self.assertIn("--proto '=https'", self.blocks[name])
                self.assertIn("--proto-redir '=https'", self.blocks[name])
                self.assertIn("--tlsv1.2", self.blocks[name])

    def test_transient_only_and_hard_wall(self):
        for name, body in self.blocks.items():
            with self.subTest(name=name):
                for term in (
                    "timeout --signal=TERM --kill-after=5s 70s",
                    "--retry 3", "--retry-delay 2", "--retry-max-time 60",
                    "--connect-timeout 10", "--max-time 20", "--fail",
                ):
                    self.assertIn(term, body)
                for forbidden in ("--retry-all-errors", "--retry-connrefused",
                                  "--insecure", "--location-trusted", "|| true",
                                  "http://", "continue-on-error"):
                    self.assertNotIn(forbidden, body)

    def test_checksum_before_unarchive(self):
        for name, body in self.blocks.items():
            with self.subTest(name=name):
                self.assertLess(body.index("curl --proto"), body.index("sha256sum --check --strict"))
                self.assertLess(body.index("sha256sum --check --strict"), body.index("tar -xzf"))
                self.assertEqual(body.count("sha256sum --check --strict"), 1)

    def test_no_change_to_mandatory_lint_and_audit(self):
        self.assertIn("set -euo pipefail", self.blocks["actionlint"])
        self.assertIn("set -euo pipefail", self.blocks["zizmor"])
        self.assertIn("Validate workflow syntax", self.data)
        self.assertIn("Audit workflow security", self.data)
        self.assertIn('"$ACTIONLINT_BIN"', self.data)
        self.assertIn('"$ZIZMOR_BIN"', self.data)
        self.assertIn("permissions:\n  contents: read", self.data)


if __name__ == "__main__":
    unittest.main()
