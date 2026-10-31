import unittest

from askai.core.support.number_format import compact_count


class CompactCountTests(unittest.TestCase):
    def test_decimal_suffixes_and_precision(self):
        for value, expected in (
            (0, "0"), (1, "1"), (999, "999"), (1000, "1K"),
            (32768, "32.8K"), (1_000_000, "1M"),
            (1_000_000_000, "1G"), (10**12, "1T"),
            (10**15, "1P"), (10**18, "1E"), (10**21, "1Z"),
            (10**24, "1Y"), (999_999, "1M"), (-32768, "-32.8K"),
        ):
            with self.subTest(value=value):
                self.assertEqual(compact_count(value), expected)
