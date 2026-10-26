"""工具箱回归测试。运行：python3 -m unittest discover -s tools/tests"""

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
REPO = TOOLS.parent
PROJECT_TOOLS = REPO / "templates/project/tools"


def run(script, *args):
    path = PROJECT_TOOLS / script if (PROJECT_TOOLS / script).exists() else TOOLS / script
    return subprocess.run(
        [sys.executable, "-I", str(path), *map(str, args)],
        capture_output=True, text=True,
    )


class TmpDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content):
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return p


class AuditMultisetTest(TmpDirCase):
    SCRIPT = "audit_multiset_integrity.py"

    def audit(self, raw, valid, excluded=None):
        args = ["--raw", raw, "--valid", valid]
        if excluded:
            args += ["--excluded", excluded]
        return run(self.SCRIPT, *args)

    def test_conserved_split_passes(self):
        raw = self.write("raw.txt", "a\nb\nc\n")
        valid = self.write("valid.txt", "a\nb\n")
        excl = self.write("excl.txt", "c\n")
        self.assertEqual(self.audit(raw, valid, excl).returncode, 0)

    def test_duplicate_in_raw_fails(self):
        raw = self.write("raw.txt", "a\na\nb\n")
        valid = self.write("valid.txt", "a\nb\n")
        self.assertEqual(self.audit(raw, valid).returncode, 1)

    def test_duplicate_in_valid_fails(self):
        raw = self.write("raw.txt", "a\nb\n")
        valid = self.write("valid.txt", "a\na\nb\n")
        self.assertEqual(self.audit(raw, valid).returncode, 1)

    def test_records_without_id_fail(self):
        raw = self.write("raw.jsonl", '{"x":1}\n{"x":2}\n')
        valid = self.write("valid.jsonl", '{"x":3}\n')
        r = self.audit(raw, valid)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("缺少", r.stderr)

    def test_empty_key_in_json_object_fails(self):
        raw = self.write("raw.json", {"": "record"})
        valid = self.write("valid.json", {"": "record"})
        r = self.audit(raw, valid)
        self.assertEqual(r.returncode, 1)
        self.assertIn("缺少", r.stderr)

    def test_missing_record_fails(self):
        raw = self.write("raw.txt", "a\nb\n")
        valid = self.write("valid.txt", "a\n")
        self.assertEqual(self.audit(raw, valid).returncode, 1)

    def test_overlap_fails(self):
        raw = self.write("raw.txt", "a\nb\n")
        valid = self.write("valid.txt", "a\nb\n")
        excl = self.write("excl.txt", "b\n")
        self.assertEqual(self.audit(raw, valid, excl).returncode, 1)

    def test_custom_id_key_jsonl_passes(self):
        raw = self.write("raw.jsonl", '{"pid":"p1"}\n{"pid":"p2"}\n')
        valid = self.write("valid.jsonl", '{"pid":"p1"}\n{"pid":"p2"}\n')
        self.assertEqual(run(self.SCRIPT, "--raw", raw, "--valid", valid, "--id-key", "pid").returncode, 0)


class VerifyGroundingTest(TmpDirCase):
    SCRIPT = "verify_grounding_assertions.py"
    TEXT = "The quick brown fox jumps over the lazy dog."

    def corpus(self, key="id"):
        return self.write("corpus.json", [{key: "d1", "text": self.TEXT}])

    def test_exact_slice_passes(self):
        ex = self.write("ex.json", [{"id": "d1", "quote": "quick", "start": 4, "end": 9}])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex).returncode, 0)

    def test_mismatched_slice_fails(self):
        ex = self.write("ex.json", [{"id": "d1", "quote": "quick", "start": 5, "end": 10}])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex).returncode, 1)

    def test_empty_extractions_fail(self):
        ex = self.write("ex.json", [])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex).returncode, 1)

    def test_id_field_applies_to_corpus(self):
        ex = self.write("ex.json", [{"doc_id": "d1", "quote": "quick", "start": 4, "end": 9}])
        r = run(self.SCRIPT, self.corpus(key="doc_id"), ex, "--id-field", "doc_id")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_full_span_fails_even_for_short_text(self):
        ex = self.write("ex.json", [{"id": "d1", "quote": self.TEXT, "start": 0, "end": len(self.TEXT)}])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex).returncode, 1)

    def test_full_span_allowed_with_flag(self):
        ex = self.write("ex.json", [{"id": "d1", "quote": self.TEXT, "start": 0, "end": len(self.TEXT)}])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex, "--allow-full-span").returncode, 0)

    def test_boolean_coordinates_fail(self):
        ex = self.write("ex.json", [{"id": "d1", "quote": "T", "start": False, "end": True}])
        self.assertEqual(run(self.SCRIPT, self.corpus(), ex).returncode, 1)


class BuildZipTest(TmpDirCase):
    SCRIPT = "build_distribution_zip.py"

    def test_secrets_are_excluded(self):
        src = self.dir / "pkg"
        self.write("pkg/paper.md", "x")
        self.write("pkg/.env", "TOKEN=1")
        self.write("pkg/.env.local", "TOKEN=2")
        self.write("pkg/keys/server.pem", "k")
        self.write("pkg/.ssh/id_rsa", "k")
        out = self.dir / "out.zip"
        r = run(self.SCRIPT, src, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.namelist(), ["paper.md"])

    def test_secret_single_file_source_is_refused(self):
        for name in (".env", "server.pem", "id_ed25519"):
            with self.subTest(name=name):
                src = self.write(name, "k")
                out = self.dir / f"{name}.zip"
                r = run(self.SCRIPT, src, out)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertFalse(out.exists())

    def test_plain_named_file_in_secret_dir_is_refused(self):
        for d in (".ssh", ".aws"):
            with self.subTest(dir=d):
                src = self.write(f"home/{d}/config", "k")
                out = self.dir / f"{d}.zip"
                r = run(self.SCRIPT, src, out)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertFalse(out.exists())

    def test_secret_dir_as_source_is_refused(self):
        self.write("home/.ssh/config", "k")
        self.assertEqual(run(self.SCRIPT, self.dir / "home/.ssh", self.dir / "out.zip").returncode, 1)

    def test_symlink_to_secret_is_not_packed(self):
        key = self.write("home/.ssh/id_rsa", "PRIVATE")
        self.write("pkg/paper.md", "x")
        (self.dir / "pkg/notes.txt").symlink_to(key)
        out = self.dir / "out.zip"
        self.assertEqual(run(self.SCRIPT, self.dir / "pkg", out).returncode, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.namelist(), ["paper.md"])

    def test_symlink_to_outside_file_is_not_packed(self):
        outside = self.write("elsewhere/data.csv", "1")
        self.write("pkg/paper.md", "x")
        (self.dir / "pkg/data.csv").symlink_to(outside)
        out = self.dir / "out.zip"
        self.assertEqual(run(self.SCRIPT, self.dir / "pkg", out).returncode, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.namelist(), ["paper.md"])

    def test_symlink_inside_source_is_packed(self):
        self.write("pkg/paper.md", "x")
        (self.dir / "pkg/link.md").symlink_to(self.dir / "pkg/paper.md")
        out = self.dir / "out.zip"
        self.assertEqual(run(self.SCRIPT, self.dir / "pkg", out).returncode, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(sorted(zf.namelist()), ["link.md", "paper.md"])

    def test_plain_single_file_source_is_packed(self):
        src = self.write("paper.md", "x")
        out = self.dir / "out.zip"
        self.assertEqual(run(self.SCRIPT, src, out).returncode, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.namelist(), ["paper.md"])

    def test_output_inside_source_is_not_packed(self):
        src = self.dir / "pkg"
        self.write("pkg/paper.md", "x")
        out = src / "dist.zip"
        self.assertEqual(run(self.SCRIPT, src, out).returncode, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.namelist(), ["paper.md"])


class WaitForVerdictTest(TmpDirCase):
    SCRIPT = REPO / "templates/project/scripts/wait-for-verdict.sh"

    def wait(self, *args):
        return subprocess.run(["bash", str(self.SCRIPT), *map(str, args)], capture_output=True, text=True)

    def test_existing_report_returns_zero(self):
        report = self.write("01-acceptance-round1.md", "> **裁决**：**ACCEPTED**\n")
        r = self.wait(report, 0)
        self.assertEqual(r.returncode, 0)
        self.assertIn("ACCEPTED", r.stdout)

    def test_missing_report_times_out_with_two(self):
        self.assertEqual(self.wait(self.dir / "nope.md", 0).returncode, 2)

    def test_tmp_file_does_not_count(self):
        self.write("01-acceptance-round1.md.tmp", "partial")
        self.assertEqual(self.wait(self.dir / "01-acceptance-round1.md", 0).returncode, 2)

    def test_bad_usage_returns_64(self):
        self.assertEqual(self.wait().returncode, 64)
        self.assertEqual(self.wait(self.dir / "x.md", "abc").returncode, 64)


if __name__ == "__main__":
    unittest.main()
