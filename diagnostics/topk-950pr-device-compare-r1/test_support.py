"""CPU-only checks for the actual measurement/transport failure boundaries."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import profile_support
import run

HERE = Path(__file__).resolve().parent


def record(seq, role, start, end):
    values = [0] * 16
    values[0] = (seq << 32) | 0x2A
    values[1] = 1
    values[2] = (1 << 32) if role == "AIV" else 0
    values[14:16] = [start, end]
    return struct.pack("<16q", *values)


def tracked(seq, namehash):
    values = [0]*8
    values[3] = seq << 32
    values[5] = namehash
    return struct.pack("<8q", *values)


class SupportTest(unittest.TestCase):
    def test_protocol_sums_distinct_tasks_and_deduplicates_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"ffts_profile.slice_0").write_bytes(record(7,"AIC",1000,4000) + record(7,"AIV",2000,6000) + record(8,"AIV",5000,8000))
            (root/"hash_dic.slice_0").write_text("11:kernel_a\n12:kernel_b\n")
            (root/"task_track.slice_0").write_bytes(tracked(7,11)+tracked(8,12))
            result = profile_support.read_profile(root, 2)
            self.assertAlmostEqual(result["latency_ms"]*1000, 8)
            self.assertEqual(result["profile_raw_record_count"], 3)
            with self.assertRaises(AssertionError):
                profile_support.read_profile(root, 1)
            (root/"hash_dic.slice_0").write_text("11:kernel_a\n")
            with self.assertRaisesRegex(AssertionError,"Unresolved"):
                profile_support.read_profile(root,2)

    def test_aicpu_time_is_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root/"device_0/data"
            data.mkdir(parents=True)
            (data.parent/"info.json.0").write_text(json.dumps({"platform_version":15,"DeviceInfo":[{"hwts_frequency":100}]}))
            (data/"ffts_profile.slice_0").write_bytes(record(7,"AIV",1000,6000))
            (data/"hash_dic.slice_0").write_text("11:kernel_a\n12:aicpu_extra\n")
            (data/"task_track.slice_0").write_bytes(tracked(7,11)+tracked(8,12))
            raw = b"".join(struct.pack("<4HQHH3L", (4<<10)|f, 0x6BD3, 8,0,t,0,0,0,0,0) for f,t in [(0,100),(1,400)])
            (data/"stars_soc.data.0.slice_0").write_bytes(raw)
            self.assertAlmostEqual(profile_support.read_profile(root,1)["latency_ms"]*1000,8)

    def test_truncated_records_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"ffts_profile.slice_0").write_bytes(b"bad")
            with self.assertRaises(ValueError):
                profile_support.parse_profile(root,1)

    def test_foreign_device_zero_process_rejected(self):
        table = "| NPU ID | Process id | Process name |\n| 0 | 999999999 | other |\n"
        with tempfile.TemporaryDirectory() as directory, patch("run.subprocess.check_output",return_value=table), patch("pathlib.Path.read_text",return_value="NSpid: 123\n"):
            with self.assertRaisesRegex(AssertionError,"another process"):
                run.check_device(Path(directory),"test")

    def test_other_cards_do_not_block(self):
        table = "| NPU ID | Process id | Process name |\n| No running processes found in NPU 0 |\n| 1 | 999999999 | other |\n"
        with tempfile.TemporaryDirectory() as directory, patch("run.subprocess.check_output",return_value=table), patch("pathlib.Path.read_text",return_value="NSpid: 123\n"):
            self.assertEqual(run.check_device(Path(directory),"test")["device0_pids"],[])

    def test_original_temp_path_rejected_and_short_path_fits(self):
        original = "/home/y00937463/topk-950pr-device-compare-r1-20261104-110915-176844/repeat-1/tmp"
        with self.assertRaisesRegex(AssertionError, "AF_UNIX"):
            run.check_socket_path(original)
        self.assertLess(run.check_socket_path("/tmp/tk-12345678"), 100)

    def test_identity_and_syntax(self):
        identity = json.loads((HERE/"identity.json").read_text())
        for name, expected in identity["tools"].items():
            raw = (HERE/name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),expected,name)
            if name.endswith(".py"):
                ast.parse(raw)
        self.assertNotIn(b"\r",(HERE/"run.sh").read_bytes())

    def test_transport_roundtrip(self):
        transport = run.load(HERE.parents[1]/"tools/b2y-result-parts/split_results.py","test_transport")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources=[]
            for i in range(3):
                source=root/(str(i)+".json")
                source.write_bytes(bytes(range(256))*20 + str(i).encode())
                sources.append((source.name,source))
            manifest=transport.split_files(sources,root/"parts",1024,"test")
            restored=transport.restore(manifest,root/"restored")
            self.assertEqual(len(restored),3)
            for name,source in sources:
                self.assertEqual(source.read_bytes(),(root/"restored"/name).read_bytes())


if __name__ == "__main__":
    unittest.main()
