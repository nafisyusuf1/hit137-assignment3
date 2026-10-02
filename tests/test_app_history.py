"""Unit tests for the picture-puzzle engine's move history."""

import unittest

from app import BuiltInPuzzleEngine


class FakeTile:
    def __init__(self, row: int, col: int) -> None:
        self.home_pos = (row, col)
        self.rotation = 0
        self.flipped = False

    def rotate_cw(self, times: int = 1) -> None:
        self.rotation = (self.rotation + 90 * times) % 360

    def flip_horizontal(self) -> None:
        self.flipped = not self.flipped


def make_engine() -> BuiltInPuzzleEngine:
    engine = BuiltInPuzzleEngine()
    engine._tiles = [
        [FakeTile(row, col) for col in range(3)]
        for row in range(3)
    ]
    return engine


def snapshot(engine: BuiltInPuzzleEngine) -> tuple:
    return tuple(
        (tile.home_pos, tile.rotation, tile.flipped)
        for row in engine._tiles
        for tile in row
    )


class PuzzleEngineHistoryTests(unittest.TestCase):
    def test_undo_and_redo_restore_swap_rotation_and_flip(self) -> None:
        engine = make_engine()
        initial_state = snapshot(engine)

        engine.swap_tiles((0, 0), (0, 1))
        engine.rotate_tile(1, 1)
        engine.flip_tile(2, 2)
        changed_state = snapshot(engine)

        self.assertTrue(engine.can_undo)
        self.assertFalse(engine.can_redo)
        self.assertTrue(engine.undo())
        self.assertTrue(engine.undo())
        self.assertTrue(engine.undo())
        self.assertEqual(snapshot(engine), initial_state)
        self.assertFalse(engine.can_undo)
        self.assertTrue(engine.can_redo)
        self.assertFalse(engine.undo())

        self.assertTrue(engine.redo())
        self.assertTrue(engine.redo())
        self.assertTrue(engine.redo())
        self.assertEqual(snapshot(engine), changed_state)
        self.assertFalse(engine.can_redo)
        self.assertFalse(engine.redo())

    def test_new_move_discards_redo_history(self) -> None:
        engine = make_engine()
        engine.swap_tiles((0, 0), (0, 1))
        engine.undo()

        engine.flip_tile(1, 1)

        self.assertFalse(engine.can_redo)
        self.assertTrue(engine.can_undo)

    def test_solve_clears_history(self) -> None:
        engine = make_engine()
        engine.swap_tiles((0, 0), (0, 1))

        engine.solve_all()

        self.assertFalse(engine.can_undo)
        self.assertFalse(engine.can_redo)


if __name__ == "__main__":
    unittest.main()
