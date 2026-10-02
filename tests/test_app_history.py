"""Unit tests for the picture-puzzle engine's move history."""

import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from app import BuiltInPuzzleEngine, PuzzleApp
from panels import clamp_preview_zoom, format_elapsed_time, make_image_preview


class FakeTile:
    def __init__(self, row: int, col: int) -> None:
        self.home_pos = (row, col)
        self.rotation = 0
        self.flipped = False

    def rotate_cw(self, times: int = 1) -> None:
        self.rotation = (self.rotation + 90 * times) % 360

    def flip_horizontal(self) -> None:
        self.flipped = not self.flipped

    def reset_orientation(self) -> None:
        self.rotation = 0
        self.flipped = False


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
    def test_image_preview_scales_proportionally_within_bounds(self) -> None:
        image = np.zeros((500, 1000, 3), dtype=np.uint8)

        preview = make_image_preview(image, max_size=(480, 360))

        self.assertEqual(preview.size, (480, 240))

    def test_preview_zoom_is_clamped_to_supported_limits(self) -> None:
        self.assertEqual(clamp_preview_zoom(1.0, 0.25), 1.25)
        self.assertEqual(clamp_preview_zoom(1.5, 0.25), 1.5)
        self.assertEqual(clamp_preview_zoom(0.5, -0.25), 0.5)

    def test_cancel_solve_keeps_game_active(self) -> None:
        app = PuzzleApp.__new__(PuzzleApp)
        app._active = True
        app._root = object()

        with patch("app.messagebox.askyesno", return_value=False) as confirm:
            app._solve()

        confirm.assert_called_once()
        self.assertTrue(app._active)

    def test_cancel_replacement_does_not_open_file_dialog(self) -> None:
        app = PuzzleApp.__new__(PuzzleApp)
        app._active = True
        app._root = object()

        with (
            patch("app.messagebox.askyesno", return_value=False) as confirm,
            patch("app.filedialog.askopenfilename") as open_file,
        ):
            app._load_image()

        confirm.assert_called_once()
        open_file.assert_not_called()
        self.assertTrue(app._active)

    def test_first_image_load_does_not_ask_replacement_confirmation(self) -> None:
        app = PuzzleApp.__new__(PuzzleApp)
        app._active = False

        with (
            patch("app.messagebox.askyesno") as confirm,
            patch("app.filedialog.askopenfilename", return_value=""),
        ):
            app._load_image()

        confirm.assert_not_called()

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

    def test_elapsed_time_format_uses_minutes_and_hours(self) -> None:
        self.assertEqual(format_elapsed_time(0), "00:00")
        self.assertEqual(format_elapsed_time(125.9), "02:05")
        self.assertEqual(format_elapsed_time(3600), "01:00:00")
        self.assertEqual(format_elapsed_time(-3), "00:00")

    def test_load_rejects_unsupported_grid_before_reading_file(self) -> None:
        engine = BuiltInPuzzleEngine()

        with self.assertRaisesRegex(ValueError, "Grid size must be 3, 4, or 5"):
            engine.load_and_prepare("not-a-real-file.png", 2)

        self.assertEqual(engine.grid_size, 3)
        self.assertIsNone(engine.original_image)

    def test_load_reports_invalid_image_and_preserves_engine_state(self) -> None:
        engine = BuiltInPuzzleEngine()
        with tempfile.NamedTemporaryFile(delete=False) as image_file:
            image_file.write(b"not an image")
            filepath = image_file.name

        try:
            with self.assertRaisesRegex(ValueError, "Invalid image file"):
                engine.load_and_prepare(filepath, 3)
        finally:
            os.unlink(filepath)

        self.assertEqual(engine.grid_size, 3)
        self.assertIsNone(engine.original_image)


if __name__ == "__main__":
    unittest.main()
