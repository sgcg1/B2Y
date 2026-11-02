"""CPU tests of probe interpretation; never import torch or launch a device."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inspect_source import collect, describe_source
from probe import analyze, check_generated_source


def fixture(rate=1000):
    cases = {}
    for repeats in [1, 16, 64, 0]:
        for mode in ["plain", "fenced", "timed"]:
            if repeats == 0 and mode != "timed":
                continue
            event = 10 + 2 * repeats + {"plain": 0, "fenced": 1, "timed": 2}[mode]
            cases[f"r{repeats}-{mode}"] = {
                "event_samples_us": [event] * 50,
                "counter_samples": [int((0.5 + 2 * repeats) * rate)] * 50
                if mode == "timed"
                else [],
            }
    return cases


class InterpretationTest(unittest.TestCase):
    def test_expected_scale_and_observer_changes(self):
        summary, checks = analyze(fixture())
        self.assertEqual(checks["observed_ticks_per_event_us_from_64_minus_16"], 1000)
        self.assertTrue(checks["rate_within_10_percent_of_documentation"])
        self.assertTrue(checks["counter_medians_increase_with_work"])
        self.assertTrue(checks["all_counter_intervals_positive"])
        self.assertTrue(checks["counter_intervals_fit_inside_events_at_documented_rate"])
        self.assertEqual(summary["r0-timed"]["counter_interval_us_at_documented_rate"], 0.5)
        self.assertEqual(summary["r1-changes"]["timed_event_delta_vs_empty_us"], 2)
        self.assertAlmostEqual(summary["r1-changes"]["timed_vs_plain_event_percent"], 100 / 6)

    def test_other_clock_domain_is_not_accepted_or_rescaled(self):
        summary, checks = analyze(fixture(rate=50))
        self.assertFalse(checks["rate_within_10_percent_of_documentation"])
        self.assertEqual(checks["observed_ticks_per_event_us_from_64_minus_16"], 50)
        self.assertEqual(summary["r0-timed"]["counter_median"], 25)

    def test_nonpositive_counter_is_flagged(self):
        cases = fixture()
        cases["r1-timed"]["counter_samples"][0] = 0
        self.assertFalse(analyze(cases)[1]["all_counter_intervals_positive"])

    def test_nonincreasing_work_is_flagged(self):
        cases = fixture()
        cases["r64-timed"]["counter_samples"] = [100] * 50
        self.assertFalse(analyze(cases)[1]["counter_medians_increase_with_work"])

    def test_invalid_event_slope_is_not_divided(self):
        cases = copy.deepcopy(fixture())
        cases["r64-timed"]["event_samples_us"] = cases["r16-timed"]["event_samples_us"]
        checks = analyze(cases)[1]
        self.assertIsNone(checks["observed_ticks_per_event_us_from_64_minus_16"])
        self.assertFalse(checks["rate_within_10_percent_of_documentation"])

    def test_nonpositive_event_samples_are_rejected(self):
        cases = fixture()
        cases["r1-plain"]["event_samples_us"][0] = 0
        with self.assertRaisesRegex(ValueError, "r1-plain"):
            analyze(cases)

    def test_generated_source_boundaries(self):
        prelude = "tileops_probe_fence(){} tileops_probe_clock(){} "
        body = "tileops_probe_fence(); tileops_probe_clock(); asc_vf_call<work>(); tileops_probe_fence(); tileops_probe_clock();"
        check_generated_source(prelude + body, 2, 16)
        with self.assertRaisesRegex(AssertionError, "source order"):
            changed = body.replace(
                "tileops_probe_fence(); tileops_probe_clock();",
                "tileops_probe_clock(); tileops_probe_fence();",
                1,
            )
            check_generated_source(prelude + changed, 2, 16)
        with self.assertRaisesRegex(AssertionError, "No VF launch"):
            check_generated_source(prelude + body.replace("asc_vf_call<work>();", ""), 2, 16)
        with self.assertRaisesRegex(AssertionError, "Plain"):
            check_generated_source(prelude + body, 0, 16)

    def test_counter_interval_exceeding_event_is_flagged(self):
        cases = fixture()
        cases["r1-timed"]["counter_samples"][0] = 1000000
        self.assertFalse(
            analyze(cases)[1]["counter_intervals_fit_inside_events_at_documented_rate"]
        )

    def test_source_export_preserves_failed_order_and_original_files(self):
        raw = b"tileops_probe_fence(){}\ntileops_probe_clock(){}\nvoid main(){\ntileops_probe_fence();\ntileops_probe_fence();\ntileops_probe_clock();\nasc_vf_call<work>();\ntileops_probe_clock();\n}\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = {
                "version": "20261102-probe1",
                "status": "failed",
                "stage": "compile:r1-timed",
            }
            (root / "probe-summary.txt").write_text(json.dumps(summary), encoding="utf-8")
            (root / "r1-timed.cpp").write_bytes(raw)
            text = collect(root)
            meta = json.loads(text.split("\n\n=====", 1)[0])
            info = meta["sources"]["r1-timed.cpp"]
            self.assertFalse(info["legacy_positional_order_check"])
            self.assertFalse(meta["source_order_root_cause_established"])
            self.assertTrue(meta["sources"]["r1-plain.cpp"]["missing"])
            self.assertEqual(info["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIn("0007: asc_vf_call<work>();", text)
            self.assertEqual((root / "r1-timed.cpp").read_bytes(), raw)

    def test_source_export_requires_primary_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe-summary.txt").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "Expected r1-timed.cpp"):
                collect(root)

    def test_source_export_does_not_invent_missing_occurrences(self):
        info = describe_source(b"tileops_probe_clock();\n")
        self.assertIsNone(info["legacy_positional_order_check"])
        self.assertEqual(len(info["clock_occurrence_offsets"]), 1)


if __name__ == "__main__":
    unittest.main()
