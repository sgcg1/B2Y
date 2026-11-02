"""CPU byte-interval counterexamples; does not execute TVM's C++ analyzer."""
import unittest


def byte_interval(lo, hi, width):
    return lo * width, hi * width + width - 1


def disjoint(a, b):
    return a[1] < b[0] or b[1] < a[0]


class ByteRangesTest(unittest.TestCase):
    def test_r2_layout_false_conflict(self):
        cache = (0, 16383)
        hist_elements = (12288, 12543)
        self.assertFalse(disjoint(cache, hist_elements))
        self.assertTrue(disjoint(cache, byte_interval(*hist_elements, 4)))

    def test_mixed_units_can_also_miss_overlap(self):
        self.assertTrue(disjoint((400, 400), (100, 100)))
        self.assertFalse(disjoint(byte_interval(400, 400, 1), byte_interval(100, 100, 4)))

    def test_widths_and_inclusive_bounds(self):
        for aw in [1, 2, 4, 8]:
            for bw in [1, 2, 4, 8]:
                for a in range(32):
                    for b in range(32):
                        # Independent oracle enumerates the actual byte addresses.
                        lhs = set(range(a * aw, (a + 1) * aw))
                        rhs = set(range(b * bw, (b + 1) * bw))
                        self.assertEqual(disjoint(byte_interval(a, a, aw),
                                                  byte_interval(b, b, bw)), lhs.isdisjoint(rhs))

    def test_histogram_and_state_are_outside_cache(self):
        cache = byte_interval(0, 16383, 1)
        for region in [(12288, 12544), (12936, 12942), (12944, 12946)]:
            self.assertTrue(disjoint(cache, byte_interval(*region, 4)))
        # Tile/lane ownership of cache writes is injective.
        addresses = [tile * 128 + lane for tile in range(128) for lane in range(128)]
        self.assertEqual(len(set(addresses)), 16384)


if __name__ == "__main__":
    unittest.main()
