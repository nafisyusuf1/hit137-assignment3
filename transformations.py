"""
transformations.py
------------------
Every change that can happen to the board is a Transformation object:

    Transformation (abstract base class)
      |-- SwapTransformation     two tiles exchange positions
      |-- RotateTransformation   a tile turns 90 / 180 / 270 degrees clockwise
      |-- FlipTransformation     a tile is mirrored horizontally or vertically

The same classes are used for two jobs:
  * scrambling the picture when an image is loaded, and
  * the player's own moves (clicks).

Because each subclass knows how to apply() and undo() itself, the board can
treat them all the same way (polymorphism) - e.g. the Solve button just calls
undo() on every transformation in reverse order.
"""

import random
from abc import ABC, abstractmethod


class Transformation(ABC):
    """Base class for anything that changes the puzzle board."""

    def __init__(self, *positions):
        self._positions = tuple(positions)

    @property
    def positions(self):
        """The grid positions this transformation touches."""
        return self._positions

    @abstractmethod
    def apply(self, board):
        """Perform the change on the board."""

    @abstractmethod
    def undo(self, board):
        """Reverse the change on the board."""

    @abstractmethod
    def describe(self):
        """Short human-readable description (used in the status bar)."""

    def __str__(self):
        return self.describe()


class SwapTransformation(Transformation):
    """Two tiles swap places."""

    def __init__(self, first, second):
        if first == second:
            raise ValueError("A swap needs two different tiles.")
        super().__init__(first, second)

    def apply(self, board):
        board.swap_positions(*self._positions)

    def undo(self, board):
        # Swapping again puts them back.
        board.swap_positions(*self._positions)

    def describe(self):
        a, b = self._positions
        return f"Swapped tiles {a + 1} and {b + 1}"


class RotateTransformation(Transformation):
    """A tile rotates clockwise by 90, 180 or 270 degrees."""

    def __init__(self, position, quarter_turns=1):
        if quarter_turns not in (1, 2, 3):
            raise ValueError("Rotation must be 1, 2 or 3 quarter turns.")
        super().__init__(position)
        self.__quarter_turns = quarter_turns

    @property
    def degrees(self):
        return self.__quarter_turns * 90

    def apply(self, board):
        board.tile_at(self._positions[0]).rotate_clockwise(self.__quarter_turns)

    def undo(self, board):
        board.tile_at(self._positions[0]).rotate_clockwise(4 - self.__quarter_turns)

    def describe(self):
        return f"Rotated tile {self._positions[0] + 1} by {self.degrees}°"


class FlipTransformation(Transformation):
    """A tile is mirrored horizontally or vertically."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    def __init__(self, position, axis=HORIZONTAL):
        if axis not in (self.HORIZONTAL, self.VERTICAL):
            raise ValueError("Axis must be 'horizontal' or 'vertical'.")
        super().__init__(position)
        self.__axis = axis

    @property
    def axis(self):
        return self.__axis

    def apply(self, board):
        tile = board.tile_at(self._positions[0])
        if self.__axis == self.HORIZONTAL:
            tile.flip_horizontal()
        else:
            tile.flip_vertical()

    def undo(self, board):
        # A flip undoes itself.
        self.apply(board)

    def describe(self):
        return f"Flipped tile {self._positions[0] + 1} {self.__axis}ly"


class TransformationGenerator:
    """
    Creates the random list of transformations used to scramble a new image.

    Rules (from the assignment brief / rubric):
      * at least one Swap, one Rotate and one Flip every time
      * number of transformations scales with grid size: n * (n - 1)
        -> 6 for 3x3, 12 for 4x4, 20 for 5x5
      * no tile is targeted twice
    """

    def __init__(self, rng=None):
        self.__rng = rng or random.Random()

    @staticmethod
    def count_for_grid(grid_size):
        return grid_size * (grid_size - 1)

    def generate(self, grid_size):
        """Return a new random list of Transformation objects."""
        tile_count = grid_size * grid_size
        count = self.count_for_grid(grid_size)

        # A swap uses 2 tiles, the others use 1. With `count` transformations
        # and no tile used twice, we can afford at most this many swaps:
        max_swaps = tile_count - count

        kinds = ["swap", "rotate", "flip"]          # guarantee all three types
        swaps = 1
        while len(kinds) < count:
            options = ["rotate", "flip"] + (["swap"] if swaps < max_swaps else [])
            kind = self.__rng.choice(options)
            swaps += kind == "swap"
            kinds.append(kind)
        self.__rng.shuffle(kinds)

        # Each tile position is handed out once only.
        free_positions = list(range(tile_count))
        self.__rng.shuffle(free_positions)

        transformations = []
        for kind in kinds:
            if kind == "swap":
                transformations.append(
                    SwapTransformation(free_positions.pop(), free_positions.pop()))
            elif kind == "rotate":
                transformations.append(
                    RotateTransformation(free_positions.pop(), self.__rng.choice((1, 2, 3))))
            else:
                axis = self.__rng.choice((FlipTransformation.HORIZONTAL,
                                          FlipTransformation.VERTICAL))
                transformations.append(FlipTransformation(free_positions.pop(), axis))
        return transformations
