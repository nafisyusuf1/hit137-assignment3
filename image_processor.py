"""
image_processor.py
------------------
All the OpenCV work for loading and preparing an image:

    load()        read JPG / PNG / BMP from disk (with error checking)
    prepare()     resize to fit the screen, then crop so the grid divides evenly
    split()       cut the picture into grid_size x grid_size tiles
    reassemble()  join the tiles back into one picture for display
"""

import os

import cv2
import numpy as np


class ImageLoadError(Exception):
    """Raised when a file can't be used as a puzzle image."""


class ImageProcessor:
    SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
    MIN_SIDE = 30   # anything smaller than this is too tiny to make a puzzle

    def __init__(self, display_size=480):
        self.__display_size = display_size

    @property
    def display_size(self):
        return self.__display_size

    # ------------------------------------------------------------------ #
    def load(self, path):
        """Read an image file and return it as a BGR numpy array."""
        if not path or not os.path.isfile(path):
            raise ImageLoadError("That file could not be found.")

        extension = os.path.splitext(path)[1].lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ImageLoadError(
                f"'{os.path.basename(path)}' is not a supported image.\n"
                "Please choose a JPG, PNG or BMP file.")

        # np.fromfile + imdecode (instead of cv2.imread) also works with
        # folder names that contain spaces or non-English characters.
        try:
            data = np.fromfile(path, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except (OSError, cv2.error) as error:
            raise ImageLoadError(f"Could not read the file:\n{error}") from error

        if image is None:
            raise ImageLoadError(
                f"'{os.path.basename(path)}' could not be opened as an image.\n"
                "The file may be damaged or not really an image.")

        height, width = image.shape[:2]
        if min(height, width) < self.MIN_SIDE:
            raise ImageLoadError(
                f"The image is too small ({width}x{height}). "
                f"Please use one at least {self.MIN_SIDE}x{self.MIN_SIDE} pixels.")
        return image

    # ------------------------------------------------------------------ #
    def prepare(self, image, grid_size):
        """
        Resize the image to fit the display area (keeping its aspect ratio),
        then centre-crop it to a square whose side divides evenly by the grid.

        Tiles have to be square, otherwise a tile rotated 90 degrees would no
        longer fit in its slot.
        """
        side = self.__display_size - (self.__display_size % grid_size)
        height, width = image.shape[:2]

        # 1. Resize (same scale for width and height -> correct aspect ratio)
        scale = side / min(height, width)
        new_width = max(side, round(width * scale))
        new_height = max(side, round(height * scale))
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)

        # 2. Centre-crop the extra width/height so the result is side x side
        top = (new_height - side) // 2
        left = (new_width - side) // 2
        return resized[top:top + side, left:left + side].copy()

    # ------------------------------------------------------------------ #
    @staticmethod
    def split(image, grid_size):
        """Cut a square image into a list of tiles (row by row)."""
        tile_size = image.shape[0] // grid_size
        tiles = []
        for row in range(grid_size):
            for col in range(grid_size):
                y, x = row * tile_size, col * tile_size
                tiles.append(image[y:y + tile_size, x:x + tile_size].copy())
        return tiles

    @staticmethod
    def reassemble(tiles, grid_size):
        """Join a row-by-row list of tiles back into one image."""
        rows = [np.hstack(tiles[r * grid_size:(r + 1) * grid_size])
                for r in range(grid_size)]
        return np.vstack(rows)
