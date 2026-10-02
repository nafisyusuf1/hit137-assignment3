"""
tile.py
-------
The Tile class represents one square piece of the puzzle.

A tile never changes its original pixels. Instead it keeps track of its
*orientation* (how many quarter turns clockwise it has been rotated and
whether it has been mirrored). The image shown on screen is rebuilt from the
original pixels + orientation every time, so rotating or flipping a tile many
times never degrades the picture.
"""

import cv2
import numpy as np


class Tile:
    """One piece of the puzzle picture."""

    def __init__(self, home_index, image):
        # Private attributes (encapsulation) - use the properties/methods below.
        self.__home_index = home_index          # where this tile belongs
        self.__original = image.copy()          # untouched pixels
        self.__rotation = 0                     # quarter turns clockwise (0-3)
        self.__flipped = False                  # mirrored horizontally?

    # ------------------------------------------------------------------ #
    # Read-only properties
    # ------------------------------------------------------------------ #
    @property
    def home_index(self):
        """The grid position this tile belongs in when the puzzle is solved."""
        return self.__home_index

    @property
    def rotation(self):
        """Number of 90 degree clockwise turns currently applied (0-3)."""
        return self.__rotation

    @property
    def flipped(self):
        """True if the tile is currently mirrored."""
        return self.__flipped

    def is_upright(self):
        """True when the tile has its original orientation."""
        return self.__rotation == 0 and not self.__flipped

    # ------------------------------------------------------------------ #
    # Orientation changes
    #
    # The current image is always:  rotate_cw^rotation( flip^flipped(original) )
    # so flips have to "pass through" the rotation, which reverses its
    # direction. That's why flipping also changes self.__rotation.
    # ------------------------------------------------------------------ #
    def rotate_clockwise(self, quarter_turns=1):
        """Rotate the tile 90 degrees clockwise `quarter_turns` times."""
        self.__rotation = (self.__rotation + quarter_turns) % 4

    def flip_horizontal(self):
        """Mirror the tile left <-> right."""
        self.__flipped = not self.__flipped
        self.__rotation = (-self.__rotation) % 4

    def flip_vertical(self):
        """Mirror the tile top <-> bottom (= horizontal flip + 180 turn)."""
        self.__flipped = not self.__flipped
        self.__rotation = (2 - self.__rotation) % 4

    def reset_orientation(self):
        """Put the tile back to its original orientation."""
        self.__rotation = 0
        self.__flipped = False

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def render(self):
        """Return the tile's pixels as they currently look (a new array)."""
        image = self.__original
        if self.__flipped:
            image = cv2.flip(image, 1)                  # 1 = horizontal flip
        if self.__rotation:
            # np.rot90 turns anticlockwise, so use a negative k for clockwise
            image = np.rot90(image, k=-self.__rotation)
        return np.ascontiguousarray(image)

    def __repr__(self):
        return (f"Tile(home={self.__home_index}, rotation={self.__rotation * 90}, "
                f"flipped={self.__flipped})")
