"""CPU regressions for the read-only probe2 exporter."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from export_complete import collect


def fixture(root):
    report = {
        "version": "20261102-probe2",
        "status": "completed",
        "cases": {},
        "postproc_captures": {},
    }
    names = [f"r{r}-{m}" for r in (1, 16, 64) for m in ("plain", "fenced", "timed")]
    for name in names + ["r0-timed"]:
        original, patched = b"// original\n", b"// instrumented\n"
        original_hash, patched_hash = [hashlib.sha256(b).hexdigest() for b in (original, patched)]
        (root / (name + "-original.cpp")).write_bytes(original)
        (root / (name + "-postproc.cpp")).write_bytes(patched)
        (root / (name + ".cpp")).write_bytes(patched)
        mode = 2 if name.endswith("timed") else 0
        report["cases"][name] = {
            "mode": mode,
            "event_samples_us": [14.0] * 50,
            "counter_samples": [600] * 50 if mode == 2 else [],
            "api_source_sha256": patched_hash,
        }
        report["postproc_captures"][name] = {
            "original_source_sha256": original_hash,
            "postproc_source_sha256": patched_hash,
        }
    (root / "probe-report.json").write_text(json.dumps(report), encoding="utf-8")


class ExportTest(unittest.TestCase):
    def test_exact_bytes_and_existing_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            exported = json.loads(json.dumps(collect(root)))
            self.assertEqual(len(exported["files"]), 21)
            for name, file in exported["files"].items():
                self.assertEqual(file["text"].encode("utf-8"), before[name])
            self.assertEqual(
                exported["api_sources"]["r1-timed"]["same_text_as"], "r1-timed-postproc.cpp"
            )
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_changed_captured_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / "r1-timed-postproc.cpp").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "Source SHA mismatch"):
                collect(root)

    def test_missing_samples_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            path = root / "probe-report.json"
            report = json.loads(path.read_text())
            report["cases"]["r1-timed"]["event_samples_us"].pop()
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "Missing event samples"):
                collect(root)

    def test_distinct_api_source_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            raw = b"// a different API capture point\n"
            (root / "r1-timed.cpp").write_bytes(raw)
            path = root / "probe-report.json"
            report = json.loads(path.read_text())
            report["cases"]["r1-timed"]["api_source_sha256"] = hashlib.sha256(raw).hexdigest()
            path.write_text(json.dumps(report), encoding="utf-8")
            exported = collect(root)
            self.assertIsNone(exported["api_sources"]["r1-timed"]["same_text_as"])
            self.assertEqual(exported["files"]["r1-timed.cpp"]["text"].encode(), raw)


if __name__ == "__main__":
    unittest.main()
