import json
from pathlib import Path
import random
import tempfile
import unittest
from split_results import restore, split_files


class ResultPartsTest(unittest.TestCase):
    def test_byte_exact_roundtrip_and_part_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = bytes(random.Random(7).randbytes(100000)) + b"\r\n\x00\xff"
            original = root / "original.txt"
            original.write_bytes(raw)
            manifest = split_files([("returned.txt", original)], root / "parts", 4096)
            info = json.loads(manifest.read_text())
            self.assertGreater(len(info["files"][0]["parts"]), 1)
            for part in info["files"][0]["parts"]:
                value = (manifest.parent / part["name"]).read_bytes()
                self.assertLessEqual(len(value), 4096)
                self.assertTrue(value.isascii())
            paths = restore(manifest, root / "restored")
            self.assertEqual(paths[0].read_bytes(), raw)
            self.assertEqual(original.read_bytes(), raw)
            with self.assertRaises(AssertionError):
                restore(manifest, root / "restored")

    def test_corrupt_or_missing_parts_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.txt"
            original.write_bytes(b"evidence" * 100)
            manifest = split_files([("returned.txt", original)], root / "parts", 1024)
            info = json.loads(manifest.read_text())
            part = manifest.parent / info["files"][0]["parts"][0]["name"]
            raw = part.read_bytes()
            part.write_bytes(b"!" + raw[1:])
            with self.assertRaises(AssertionError):
                restore(manifest, root / "out")
            self.assertFalse((root / "out").exists())
            part.unlink()
            with self.assertRaises(FileNotFoundError):
                restore(manifest, root / "out")


if __name__ == "__main__":
    unittest.main()
