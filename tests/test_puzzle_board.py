"""Unit tests for puzzle_board.py."""

import random
import unittest

from puzzle_board import PuzzleBoard


class FakeTile:
    """Small Tile replacement that keeps these tests independent of OpenCV."""

    def __init__(self, original_index: int) -> None:
        self.original_index = original_index
        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

    @property
    def correctly_oriented(self) -> bool:
        return (
            self.rotation == 0
            and not self.flipped_horizontal
            and not self.flipped_vertical
        )

    def rotate_clockwise(self, quarter_turns: int = 1) -> None:
        self.rotation = (self.rotation + 90 * quarter_turns) % 360

    def flip(self, horizontal: bool = True) -> None:
        if horizontal:
            self.flipped_horizontal = not self.flipped_horizontal
        else:
            self.flipped_vertical = not self.flipped_vertical

    def reset_orientation(self) -> None:
        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False


def scrambled_board() -> PuzzleBoard:
    tiles = [FakeTile(i) for i in range(9)]
    tiles[0], tiles[1] = tiles[1], tiles[0]
    return PuzzleBoard(tiles, 3, rng=random.Random(1))


class PuzzleBoardTests(unittest.TestCase):
    def test_new_scrambled_board_has_zero_moves(self) -> None:
        board = scrambled_board()
        self.assertEqual(board.moves, 0)
        self.assertEqual(board.incorrect_count, 2)
        self.assertFalse(board.solved)

    def test_swap_counts_one_move_and_can_complete_board(self) -> None:
        board = scrambled_board()
        self.assertTrue(board.swap_positions(0, 1))
        self.assertEqual(board.moves, 1)
        self.assertEqual(board.incorrect_count, 0)
        self.assertTrue(board.solved)

    def test_rotation_counts_as_one_move(self) -> None:
        board = scrambled_board()
        board.rotate_at(2)
        self.assertEqual(board.moves, 1)
        self.assertEqual(board.tile_at(2).rotation, 90)
        self.assertFalse(board.is_position_correct(2))

    def test_four_rotations_restore_orientation(self) -> None:
        board = scrambled_board()
        for _ in range(4):
            board.rotate_at(2)
        self.assertEqual(board.tile_at(2).rotation, 0)
        self.assertTrue(board.is_position_correct(2))
        self.assertEqual(board.moves, 4)

    def test_flip_counts_one_move_and_two_flips_restore_tile(self) -> None:
        board = scrambled_board()
        board.flip_at(2)
        self.assertEqual(board.moves, 1)
        self.assertFalse(board.is_position_correct(2))
        board.flip_at(2)
        self.assertEqual(board.moves, 2)
        self.assertTrue(board.is_position_correct(2))

    def test_position_and_orientation_are_both_required(self) -> None:
        board = scrambled_board()
        self.assertFalse(board.is_position_correct(0))
        self.assertTrue(board.is_position_correct(2))
        board.rotate_at(2)
        self.assertFalse(board.is_position_correct(2))

    def test_hint_identifies_wrong_tile_and_home(self) -> None:
        board = scrambled_board()
        current, home = board.use_hint()
        self.assertFalse(board.is_position_correct(current))
        self.assertEqual(board.tile_at(current).original_index, home)
        self.assertEqual(board.hints_remaining, 2)

    def test_only_three_hints_are_allowed(self) -> None:
        board = scrambled_board()
        self.assertIsNotNone(board.use_hint())
        self.assertIsNotNone(board.use_hint())
        self.assertIsNotNone(board.use_hint())
        self.assertIsNone(board.use_hint())
        self.assertEqual(board.hints_used, 3)
        self.assertEqual(board.hints_remaining, 0)

    def test_next_move_clears_hint(self) -> None:
        board = scrambled_board()
        board.use_hint()
        self.assertIsNotNone(board.hint)
        board.rotate_at(2)
        self.assertIsNone(board.hint)

    def test_solve_restores_everything_and_clears_moves(self) -> None:
        board = scrambled_board()
        board.rotate_at(2)
        board.flip_at(3)
        board.use_hint()
        board.solve()
        self.assertTrue(board.solved)
        self.assertEqual(board.moves, 0)
        self.assertEqual(board.incorrect_count, 0)
        self.assertIsNone(board.hint)
        self.assertEqual(
            [tile.original_index for tile in board.tiles],
            list(range(9)),
        )
        self.assertTrue(all(tile.correctly_oriented for tile in board.tiles))

    def test_player_move_is_rejected_after_completion(self) -> None:
        board = scrambled_board()
        board.solve()
        self.assertFalse(board.rotate_at(0))
        self.assertFalse(board.flip_at(0))
        self.assertFalse(board.swap_positions(0, 1))
        self.assertEqual(board.moves, 0)

    def test_invalid_position_is_rejected(self) -> None:
        board = scrambled_board()
        with self.assertRaises(IndexError):
            board.rotate_at(9)


if __name__ == "__main__":
    unittest.main()
