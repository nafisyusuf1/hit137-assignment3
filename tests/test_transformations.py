"""Tests for grid-scaled puzzle scrambling transformations."""

import random
import unittest

from transformations import (
    FlipTransformation,
    RotateTransformation,
    SwapTransformation,
    TransformationGenerator,
)


class FakeTile:
    def __init__(self, row: int, col: int) -> None:
        self.home_pos = (row, col)
        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

    def rotate_clockwise(self, quarter_turns: int = 1) -> None:
        self.rotation = (self.rotation + quarter_turns * 90) % 360

    def flip_horizontal(self) -> None:
        self.flipped_horizontal = not self.flipped_horizontal

    def flip_vertical(self) -> None:
        self.flipped_vertical = not self.flipped_vertical

    def reset_orientation(self) -> None:
        self.rotation = 0
        self.flipped_horizontal = False
        self.flipped_vertical = False

    def is_orientation_correct(self) -> bool:
        return (
            self.rotation == 0
            and not self.flipped_horizontal
            and not self.flipped_vertical
        )


class TransformationGeneratorTests(unittest.TestCase):
    def test_count_scales_with_grid_and_each_tile_is_targeted_once(self) -> None:
        expected_counts = {3: 6, 4: 12, 5: 20}

        for grid_size, expected_count in expected_counts.items():
            for seed in range(10):
                with self.subTest(grid_size=grid_size, seed=seed):
                    generator = TransformationGenerator(random.Random(seed))
                    transformations = generator.generate(grid_size)
                    targeted_positions = [
                        position
                        for transformation in transformations
                        for position in transformation.positions
                    ]

                    self.assertEqual(len(transformations), expected_count)
                    self.assertEqual(
                        len(targeted_positions),
                        len(set(targeted_positions)),
                    )
                    self.assertEqual(
                        {type(transformation) for transformation in transformations},
                        {
                            SwapTransformation,
                            RotateTransformation,
                            FlipTransformation,
                        },
                    )

    def test_generated_transformations_can_be_applied_and_solved_by_engine(self) -> None:
        from app import BuiltInPuzzleEngine

        engine = BuiltInPuzzleEngine()
        engine._grid_size = 3
        engine._tiles = [
            [FakeTile(row, col) for col in range(3)]
            for row in range(3)
        ]

        engine._scramble_tiles()

        self.assertGreater(len(engine.get_incorrect_positions()), 0)
        self.assertFalse(engine.can_undo)
        engine.solve_all()
        self.assertEqual(engine.get_incorrect_positions(), [])


if __name__ == "__main__":
    unittest.main()
