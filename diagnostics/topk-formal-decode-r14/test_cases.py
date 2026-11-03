"""Verify expanded cases actually exercise the advertised coarse-bucket paths."""
import math
import struct
import unittest
from cases import build_cases, validation_cases

class CaseTest(unittest.TestCase):
    def test_deterministic_branch_coverage(self):
        cases = build_cases()
        self.assertEqual(cases, build_cases())
        self.assertEqual(len(cases), 10)
        for case in cases:
            self.assertEqual(len(case["values"]), 16384)
            start, stop = case["window"]
            hist = [0] * 256
            for value in case["values"][start:stop]:
                value = struct.unpack("f", struct.pack("f", value))[0]
                bits = struct.unpack("H", struct.pack("e", value))[0]
                key = 32768 if bits & 32767 == 0 else (~bits & 65535) if bits >> 15 else bits | 32768
                hist[key >> 8] += 1
            before = 0
            boundary = 0
            for bucket in range(255, -1, -1):
                if before <= 2048 < before + hist[bucket]:
                    boundary = hist[bucket]
                    break
                before += hist[bucket]
            if case["overflow"] is not None:
                self.assertEqual(boundary > 2048, case["overflow"], case["label"])
            if case["label"].startswith("boundary-"):
                self.assertEqual(boundary, int(case["label"].split("-")[1]))
            if case["label"] == "narrow-overflow":
                self.assertEqual(before, 1024)
                self.assertEqual(boundary, 3072)
                self.assertTrue(max(case["values"][:start]) > max(case["values"][start:stop]))
    def test_extra_validation_cases(self):
        extra = validation_cases()
        self.assertEqual(len(extra), 4)
        self.assertTrue(any(math.isnan(x) for x in extra[0][1]))
        self.assertEqual([max(0, stop - start) for _, _, start, stop in extra], [16384, 50, 0, 0])

if __name__ == "__main__":
    unittest.main()
