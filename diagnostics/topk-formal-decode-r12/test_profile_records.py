"""CPU tests for complete-call grouping, tails and timestamp precision."""
import unittest
from decimal import Decimal
from profile_records import summarize_rows


def records(calls=60, kernels=4):
    rows = []
    for call in range(calls):
        for stage in range(kernels):
            # Large device clocks must not lose sub-us gaps through float parsing.
            rows.append({"Name": "main_kernel", "Stream Id": "7",
                         "Start Time(us)": f"179334701836{call:04d}.{stage * 200:03d}",
                         "Duration(us)": "0.125"})
    return rows


class ProfileRecordsTest(unittest.TestCase):
    def test_full_pipeline_chronological_tail(self):
        rows = records()
        result = summarize_rows(list(reversed(rows)), 4)
        self.assertEqual(result["captured_records"], 240)
        self.assertEqual(result["selected_records"][0], rows[40])
        self.assertEqual(result["sum_kernel_median_us"], .5)
        self.assertEqual(result["gap_sum_median_us"], .225)
        self.assertEqual(result["envelope_median_us"], .725)
        self.assertEqual(len(result["calls"]), 50)

    def test_single_kernel_envelope(self):
        result = summarize_rows(records(kernels=1), 1)
        self.assertEqual(result["envelope_median_us"], .125)
        self.assertEqual(result["gap_sum_median_us"], 0)

    def test_incomplete_capture_is_rejected(self):
        for rows in [records(calls=49), records()[:-1], records(calls=61)]:
            with self.assertRaises(AssertionError):
                summarize_rows(rows, 4)

    def test_overlap_and_multiple_streams_rejected(self):
        rows = records()
        rows[-1]["Start Time(us)"] = rows[-2]["Start Time(us)"]
        with self.assertRaises(AssertionError):
            summarize_rows(rows, 4)

    def test_same_call_sum_is_not_sum_of_stage_medians(self):
        rows = []
        for call in range(50):
            durations = [1, 100, 1, 1] if call < 20 else [100, 1, 1, 1] if call < 40 else [1, 1, 1, 1]
            clock = Decimal(1000 + call * 1000)
            for duration in durations:
                rows.append({"Start Time(us)": str(clock), "Duration(us)": str(duration)})
                clock += Decimal(duration) + Decimal("0.1")
        result = summarize_rows(rows, 4)
        self.assertEqual(result["sum_kernel_median_us"], 103)
        self.assertEqual(sum(result["stage_median_us"].values()), 4)

    def test_wrong_block_order_is_rejected(self):
        rows = records()
        for i, row in enumerate(rows):
            row["Block Num"] = str([4, 1, 4, 1][i % 4])
        summarize_rows(rows, 4)
        rows[-1]["Block Num"] = "4"
        with self.assertRaises(AssertionError):
            summarize_rows(rows, 4)

    def test_leading_partial_retained_and_tail_marked_for_review(self):
        rows = records()
        for i, row in enumerate(rows):
            row["Block Num"] = str([4, 1, 4, 1][i % 4])
        result = summarize_rows(rows[1:], 4)
        self.assertEqual(result["captured_records"], 239)
        self.assertEqual(result["leading_partial_records"], rows[1:4])
        self.assertEqual(result["selected_records"], rows[-200:])
        self.assertIn("provisional", result["boundary_review"])

    def test_trailing_partial_not_misclassified_as_leading(self):
        rows = records()
        for i, row in enumerate(rows):
            row["Block Num"] = str([4, 1, 4, 1][i % 4])
        with self.assertRaises(AssertionError):
            summarize_rows(rows[:-1], 4)
        rows = records()
        rows[-1]["Stream Id"] = "9"
        with self.assertRaises(AssertionError):
            summarize_rows(rows, 4)


if __name__ == "__main__":
    unittest.main()
