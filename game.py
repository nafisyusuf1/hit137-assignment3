"""Gameplay controller for the HIT137 picture puzzle.

``PuzzleGame`` translates player actions into ``PuzzleBoard`` operations.  It
contains no Tkinter widgets, message boxes, or drawing code, so it can be unit
tested independently from the interface.
"""

from __future__ import annotations

from typing import Any, Optional

from puzzle_board import PuzzleBoard


class PuzzleGame:
    """Control one playable round without depending on the GUI."""

    def __init__(self, board: PuzzleBoard) -> None:
        self.__board = board
        self.__selected_position: Optional[int] = None

    @property
    def board(self) -> PuzzleBoard:
        return self.__board

    @property
    def selected_position(self) -> Optional[int]:
        return self.__selected_position

    @property
    def locked(self) -> bool:
        return self.__board.solved

    def left_click(self, position: int) -> str:
        """Select, deselect, or swap according to a left-click.

        Returns ``"selected"``, ``"deselected"``, ``"swapped"``, or
        ``"ignored"`` so the GUI knows what happened.
        """
        if not self.__can_use(position):
            return "ignored"

        if self.__selected_position is None:
            self.__selected_position = position
            return "selected"

        if self.__selected_position == position:
            self.__selected_position = None
            return "deselected"

        first = self.__selected_position
        self.__selected_position = None
        return "swapped" if self.__board.swap_positions(first, position) else "ignored"

    def right_click(self, position: int) -> bool:
        """Rotate the clicked tile 90 degrees clockwise."""
        if not self.__can_use(position):
            return False
        changed = self.__board.rotate_at(position, quarter_turns=1)
        if changed and self.__board.solved:
            self.__selected_position = None
        return changed

    def shift_left_click(self, position: int) -> bool:
        """Flip the clicked tile horizontally."""
        if not self.__can_use(position):
            return False
        changed = self.__board.flip_at(position, horizontal=True)
        if changed and self.__board.solved:
            self.__selected_position = None
        return changed

    def request_hint(self) -> Optional[tuple[int, int]]:
        if self.locked:
            return None
        return self.__board.use_hint()

    def solve(self) -> bool:
        """Solve the round, clear selection, and lock puzzle input."""
        if self.locked:
            return False
        self.__selected_position = None
        return self.__board.solve()

    def reset_selection(self) -> None:
        self.__selected_position = None

    def status(self) -> dict[str, Any]:
        """Return the values that the GUI needs for counters and controls."""
        return {
            "moves": self.__board.moves,
            "incorrect_tiles": self.__board.incorrect_count,
            "hints_remaining": self.__board.hints_remaining,
            "selected_position": self.__selected_position,
            "hint": self.__board.hint,
            "solved": self.__board.solved,
            "locked": self.locked,
        }

    def __can_use(self, position: int) -> bool:
        if self.locked:
            return False
        # tile_at performs consistent type/range validation.
        self.__board.tile_at(position)
        return True
