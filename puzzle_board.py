"""Board state and rules for the HIT137 picture puzzle.

This module deliberately contains no Tkinter or OpenCV drawing code.  It works
with Tile objects supplied by ``tile.py``.  A compatible tile exposes:

* ``original_index`` -- the position where the tile belongs;
* ``correctly_oriented`` -- True only at its original rotation/flip state;
* ``rotate_clockwise(quarter_turns)``;
* ``flip(horizontal=True)``; and
* ``reset_orientation()``.
"""

from __future__ import annotations

import random
from typing import Any, Iterable, Optional, Sequence


class PuzzleBoard:
    """Own the tile grid, counters, hints, correctness, and solve rules."""

    MAX_HINTS = 3

    def __init__(
        self,
        tiles: Sequence[Any],
        grid_size: int,
        rng: Optional[random.Random] = None,
    ) -> None:
        if grid_size not in (3, 4, 5):
            raise ValueError("Grid size must be 3, 4, or 5.")
        if len(tiles) != grid_size * grid_size:
            raise ValueError("The tile count must equal grid_size squared.")

        self.__tiles = list(tiles)
        self.__grid_size = grid_size
        self.__moves = 0
        self.__hints_used = 0
        self.__hint: Optional[tuple[int, int]] = None
        self.__rng = rng or random.Random()
        self.__solved = self.incorrect_count == 0

    @property
    def tiles(self) -> tuple[Any, ...]:
        """Return a read-only view of the current tile order."""
        return tuple(self.__tiles)

    @property
    def grid_size(self) -> int:
        return self.__grid_size

    @property
    def moves(self) -> int:
        return self.__moves

    @property
    def hints_used(self) -> int:
        return self.__hints_used

    @property
    def hints_remaining(self) -> int:
        return max(0, self.MAX_HINTS - self.__hints_used)

    @property
    def hint(self) -> Optional[tuple[int, int]]:
        """Return ``(current_position, home_position)`` for the active hint."""
        return self.__hint

    @property
    def solved(self) -> bool:
        return self.__solved

    @property
    def incorrect_count(self) -> int:
        return sum(
            not self.is_position_correct(position)
            for position in range(len(self.__tiles))
        )

    def tile_at(self, position: int) -> Any:
        self.__validate_position(position)
        return self.__tiles[position]

    def is_position_correct(self, position: int) -> bool:
        """Check both the tile's location and its complete orientation."""
        self.__validate_position(position)
        tile = self.__tiles[position]
        return (
            tile.original_index == position
            and bool(tile.correctly_oriented)
        )

    def swap_positions(
        self, first: int, second: int, count_move: bool = True
    ) -> bool:
        """Swap two positions; a player swap counts as exactly one move."""
        self.__validate_position(first)
        self.__validate_position(second)
        if first == second:
            return False
        if count_move and self.__solved:
            return False

        self.__tiles[first], self.__tiles[second] = (
            self.__tiles[second],
            self.__tiles[first],
        )
        self.__finish_change(count_move)
        return True

    def rotate_at(
        self,
        position: int,
        quarter_turns: int = 1,
        count_move: bool = True,
    ) -> bool:
        """Rotate a tile clockwise; any non-zero player rotation is one move."""
        self.__validate_position(position)
        turns = quarter_turns % 4
        if turns == 0:
            return False
        if count_move and self.__solved:
            return False

        self.__tiles[position].rotate_clockwise(turns)
        self.__finish_change(count_move)
        return True

    def flip_at(
        self,
        position: int,
        horizontal: bool = True,
        count_move: bool = True,
    ) -> bool:
        """Flip one tile horizontally or vertically and count one player move."""
        self.__validate_position(position)
        if count_move and self.__solved:
            return False

        self.__tiles[position].flip(horizontal=horizontal)
        self.__finish_change(count_move)
        return True

    def use_hint(self) -> Optional[tuple[int, int]]:
        """Mark one wrong tile and its home position, up to three times."""
        if self.__solved or self.__hints_used >= self.MAX_HINTS:
            return None

        incorrect = [
            position
            for position in range(len(self.__tiles))
            if not self.is_position_correct(position)
        ]
        if not incorrect:
            self.__solved = True
            return None

        current = self.__rng.choice(incorrect)
        home = self.__tiles[current].original_index
        self.__hint = (current, home)
        self.__hints_used += 1
        return self.__hint

    def clear_hint(self) -> None:
        self.__hint = None

    def solve(self) -> bool:
        """Restore every tile and orientation, then clear the move score."""
        ordered: list[Optional[Any]] = [None] * len(self.__tiles)
        for tile in self.__tiles:
            home = tile.original_index
            if not isinstance(home, int) or not 0 <= home < len(ordered):
                raise ValueError("Every tile must have a valid original_index.")
            if ordered[home] is not None:
                raise ValueError("Tile original_index values must be unique.")
            tile.reset_orientation()
            ordered[home] = tile

        if any(tile is None for tile in ordered):
            raise ValueError("A tile is missing from the board.")

        self.__tiles = [tile for tile in ordered if tile is not None]
        self.__moves = 0
        self.__hint = None
        self.__solved = True
        return True

    def reset(self, tiles: Optional[Iterable[Any]] = None) -> None:
        """Reset counters for a new round, optionally replacing all tiles."""
        if tiles is not None:
            replacement = list(tiles)
            if len(replacement) != self.__grid_size * self.__grid_size:
                raise ValueError("The tile count must equal grid_size squared.")
            self.__tiles = replacement
        self.__moves = 0
        self.__hints_used = 0
        self.__hint = None
        self.__solved = self.incorrect_count == 0

    def __finish_change(self, count_move: bool) -> None:
        if count_move:
            self.__moves += 1
            self.__hint = None
        self.__solved = self.incorrect_count == 0

    def __validate_position(self, position: int) -> None:
        if not isinstance(position, int):
            raise TypeError("Tile position must be an integer.")
        if not 0 <= position < len(self.__tiles):
            raise IndexError("Tile position is outside the puzzle board.")
