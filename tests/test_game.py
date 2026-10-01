"""Unit tests for game.py."""

import unittest

from game import PuzzleGame
from puzzle_board import PuzzleBoard


class FakeTile:
    def __init__(self, original_index: int) -> None:
        self.original_index = original_index
        self.rotation = 0
        self.flipped = False

    @property
    def correctly_oriented(self) -> bool:
        return self.rotation == 0 and not self.flipped

    def rotate_clockwise(self, quarter_turns: int = 1) -> None:
        self.rotation = (self.rotation + 90 * quarter_turns) % 360

    def flip(self, horizontal: bool = True) -> None:
        self.flipped = not self.flipped

    def reset_orientation(self) -> None:
        self.rotation = 0
        self.flipped = False


def make_game() -> PuzzleGame:
    tiles = [FakeTile(i) for i in range(9)]
    tiles[0], tiles[1] = tiles[1], tiles[0]
    return PuzzleGame(PuzzleBoard(tiles, 3))


class PuzzleGameTests(unittest.TestCase):
    def test_first_click_selects_without_counting_move(self) -> None:
        game = make_game()
        self.assertEqual(game.left_click(0), "selected")
        self.assertEqual(game.selected_position, 0)
        self.assertEqual(game.board.moves, 0)

    def test_clicking_selected_tile_deselects_without_move(self) -> None:
        game = make_game()
        game.left_click(0)
        self.assertEqual(game.left_click(0), "deselected")
        self.assertIsNone(game.selected_position)
        self.assertEqual(game.board.moves, 0)

    def test_clicking_second_tile_swaps_and_clears_selection(self) -> None:
        game = make_game()
        game.left_click(0)
        self.assertEqual(game.left_click(1), "swapped")
        self.assertIsNone(game.selected_position)
        self.assertEqual(game.board.moves, 1)
        self.assertTrue(game.board.solved)

    def test_right_click_rotates_and_counts_one_move(self) -> None:
        game = make_game()
        self.assertTrue(game.right_click(2))
        self.assertEqual(game.board.tile_at(2).rotation, 90)
        self.assertEqual(game.board.moves, 1)

    def test_shift_left_click_flips_and_counts_one_move(self) -> None:
        game = make_game()
        self.assertTrue(game.shift_left_click(2))
        self.assertTrue(game.board.tile_at(2).flipped)
        self.assertEqual(game.board.moves, 1)

    def test_game_requests_no_more_than_three_hints(self) -> None:
        game = make_game()
        self.assertIsNotNone(game.request_hint())
        self.assertIsNotNone(game.request_hint())
        self.assertIsNotNone(game.request_hint())
        self.assertIsNone(game.request_hint())

    def test_solve_clears_selection_moves_and_locks_game(self) -> None:
        game = make_game()
        game.left_click(0)
        game.right_click(2)
        self.assertTrue(game.solve())
        self.assertIsNone(game.selected_position)
        self.assertEqual(game.board.moves, 0)
        self.assertEqual(game.board.incorrect_count, 0)
        self.assertTrue(game.locked)

    def test_completed_game_rejects_more_input(self) -> None:
        game = make_game()
        game.solve()
        self.assertEqual(game.left_click(0), "ignored")
        self.assertFalse(game.right_click(0))
        self.assertFalse(game.shift_left_click(0))
        self.assertIsNone(game.request_hint())
        self.assertEqual(game.board.moves, 0)

    def test_status_supplies_gui_values(self) -> None:
        game = make_game()
        game.left_click(0)
        status = game.status()
        self.assertEqual(status["moves"], 0)
        self.assertEqual(status["incorrect_tiles"], 2)
        self.assertEqual(status["hints_remaining"], 3)
        self.assertEqual(status["selected_position"], 0)
        self.assertFalse(status["solved"])


if __name__ == "__main__":
    unittest.main()
