"""Tests for keyboard navigation within the puzzle grid."""

import unittest

from app import move_grid_focus


class KeyboardControlTests(unittest.TestCase):
    def test_focus_moves_in_each_direction(self) -> None:
        self.assertEqual(move_grid_focus((1, 1), -1, 0, 3), (0, 1))
        self.assertEqual(move_grid_focus((1, 1), 1, 0, 3), (2, 1))
        self.assertEqual(move_grid_focus((1, 1), 0, -1, 3), (1, 0))
        self.assertEqual(move_grid_focus((1, 1), 0, 1, 3), (1, 2))

    def test_focus_stays_inside_grid_at_edges(self) -> None:
        self.assertEqual(move_grid_focus((0, 0), -1, 0, 3), (0, 0))
        self.assertEqual(move_grid_focus((0, 0), 0, -1, 3), (0, 0))
        self.assertEqual(move_grid_focus((4, 4), 1, 0, 5), (4, 4))
        self.assertEqual(move_grid_focus((4, 4), 0, 1, 5), (4, 4))


if __name__ == "__main__":
    unittest.main()
