"""Unit tests for persistent puzzle best times."""

import json
import tempfile
import unittest
from pathlib import Path

from best_times import BestTimes


class BestTimesTests(unittest.TestCase):
    def test_records_fastest_time_and_persists_by_grid_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scores" / "best_times.json"
            records = BestTimes(path)

            self.assertEqual(records.best_for(3), None)
            self.assertEqual(records.record(3, 72.5), (True, 72.5))
            self.assertEqual(records.record(3, 80), (False, 72.5))
            self.assertEqual(records.record(4, 91), (True, 91.0))
            self.assertEqual(BestTimes(path).best_for(3), 72.5)
            self.assertEqual(BestTimes(path).best_for(4), 91.0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {
                "3": 72.5,
                "4": 91.0,
            })

    def test_rejects_invalid_grid_sizes_and_elapsed_times(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            records = BestTimes(Path(temp_dir) / "times.json")

            for invalid_size in (True, 2, 6, 3.0):
                with self.subTest(grid_size=invalid_size):
                    with self.assertRaises(ValueError):
                        records.best_for(invalid_size)

            for invalid_time in (True, -1, float("inf"), float("nan")):
                with self.subTest(elapsed=invalid_time):
                    with self.assertRaises(ValueError):
                        records.record(3, invalid_time)

    def test_corrupt_best_time_file_reports_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "times.json"
            path.write_text("not valid JSON", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                BestTimes(path).best_for(3)


if __name__ == "__main__":
    unittest.main()
