"""CPU tests of probe interpretation; never import torch or launch a device."""

import copy
import unittest

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


if __name__ == "__main__":
    unittest.main()
