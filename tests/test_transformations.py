"""Tests for grid-scaled puzzle scrambling transformations."""

import random
import unittest

from transformations import (
    FlipTransformation,
    RotateTransformation,
    SwapTransformation,
    TransformationGenerator,
)


class TransformationGeneratorTests(unittest.TestCase):
    @staticmethod
    def make_engine(scramble=False):
        """A real engine on a random-pixel 3x3 image (scrambled if asked)."""
        import numpy as np
        from app import BuiltInPuzzleEngine

        image = np.random.default_rng(1).integers(0, 255, (300, 300, 3), dtype=np.uint8)
        engine = BuiltInPuzzleEngine(display_max_size=300, rng=random.Random(3))
        engine.load_array(image, 3, scramble=scramble)
        return engine

    @staticmethod
    def state(engine):
        return tuple((t.home_index, t.rotation, t.flipped) for t in engine.tiles)

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

    def test_difficulty_scales_scramble_strength_for_every_grid(self) -> None:
        expected_counts = {
            3: {"Easy": 3, "Normal": 6, "Hard": 8},
            4: {"Easy": 6, "Normal": 12, "Hard": 15},
            5: {"Easy": 10, "Normal": 20, "Hard": 24},
        }
        for grid_size, counts in expected_counts.items():
            for difficulty, expected_count in counts.items():
                for seed in range(10):
                    with self.subTest(
                        grid_size=grid_size,
                        difficulty=difficulty,
                        seed=seed,
                    ):
                        transformations = TransformationGenerator(
                            random.Random(seed)
                        ).generate(grid_size, difficulty)
                        positions = [
                            position
                            for transformation in transformations
                            for position in transformation.positions
                        ]
                        self.assertEqual(len(transformations), expected_count)
                        self.assertEqual(len(positions), len(set(positions)))

    def test_generator_rejects_unknown_difficulty(self) -> None:
        with self.assertRaisesRegex(ValueError, "Difficulty must be one of"):
            TransformationGenerator().generate(3, "Extreme")

    def test_generated_transformations_can_be_applied_and_solved_by_engine(self) -> None:
        engine = self.make_engine(scramble=True)

        self.assertGreater(len(engine.get_incorrect_positions()), 0)
        self.assertFalse(engine.can_undo)
        engine.solve_all()
        self.assertEqual(engine.get_incorrect_positions(), [])

    def test_restart_restores_same_scramble_and_clears_move_history(self) -> None:
        engine = self.make_engine(scramble=True)
        initial_scramble = self.state(engine)

        engine.swap_tiles((0, 0), (0, 1))
        engine.rotate_tile(1, 1)
        self.assertTrue(engine.can_undo)

        self.assertTrue(engine.restart())
        restarted_state = self.state(engine)
        self.assertEqual(restarted_state, initial_scramble)
        self.assertFalse(engine.can_undo)
        self.assertFalse(engine.can_redo)

    def test_restart_without_a_loaded_scramble_returns_false(self) -> None:
        engine = self.make_engine()

        self.assertFalse(engine.restart())


if __name__ == "__main__":
    unittest.main()
