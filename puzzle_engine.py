"""
puzzle_engine.py
----------------
Connects the shared classes so the GUI has one object to talk to:

    ImageProcessor (image_processor.py)  -> load, resize, crop, split, reassemble
    Tile           (tile.py)             -> one piece and its orientation
    PuzzleBoard    (puzzle_board.py)     -> tile order, correctness, hints, solve
    PuzzleGame     (game.py)             -> select / swap / rotate / flip rules
    Transformation (transformations.py)  -> random scramble + undo/redo moves

PuzzleApp (app.py) only calls PuzzleEngine, so the GUI never touches the
tiles or OpenCV directly.
"""

from game import PuzzleGame
from image_processor import ImageLoadError, ImageProcessor
from puzzle_board import PuzzleBoard
from tile import Tile
from transformations import (FlipTransformation, RotateTransformation,
                             SwapTransformation, TransformationGenerator)


class GridTile(Tile):
    """
    A Tile that also knows its grid size, so it can report its home as a
    (row, col) pair. It inherits all pixel/orientation logic from Tile and
    adds the names PuzzleBoard expects (original_index, correctly_oriented,
    flip) - inheritance used to make two classes work together.
    """

    def __init__(self, home_index, image, grid_size):
        super().__init__(home_index, image)
        self.__grid_size = grid_size

    @property
    def original_index(self):
        return self.home_index

    @property
    def correctly_oriented(self):
        return self.is_upright()

    @property
    def home_pos(self):
        return divmod(self.home_index, self.__grid_size)

    def flip(self, horizontal=True):
        if horizontal:
            self.flip_horizontal()
        else:
            self.flip_vertical()


class PuzzleEngine:
    """Everything the GUI needs for one puzzle, built from the shared classes."""

    GRID_SIZES = (3, 4, 5)

    def __init__(self, display_max_size=450, rng=None):
        self.__processor = ImageProcessor(display_max_size)
        self.__generator = TransformationGenerator(rng)
        self.__rng = rng
        self.__grid_size = 3
        self.__difficulty = "Normal"
        self.__original = None
        self.__board = None
        self.__game = None
        self.__scramble = []
        self.__undo_stack = []
        self.__redo_stack = []

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def original_image(self):
        return self.__original

    @property
    def grid_size(self):
        return self.__grid_size

    @property
    def difficulty(self):
        return self.__difficulty

    @property
    def board(self):
        return self.__board

    @property
    def tiles(self):
        return self.__board.tiles if self.__board else ()

    @property
    def selected_pos(self):
        """Currently selected tile as (row, col), or None."""
        if self.__game is None or self.__game.selected_position is None:
            return None
        return self.__to_rc(self.__game.selected_position)

    @property
    def can_undo(self):
        return bool(self.__undo_stack)

    @property
    def can_redo(self):
        return bool(self.__redo_stack)

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    def decode_image(self, filepath):
        """Read an image file with ImageProcessor (raises ValueError if bad)."""
        try:
            return self.__processor.load(filepath)
        except ImageLoadError as error:
            raise ValueError(f"Invalid image file. {error}") from error

    def prepare_preview(self, image, grid_size):
        """The resized + cropped picture exactly as it will be used."""
        return self.__processor.prepare(image, grid_size)

    def load_and_prepare(self, filepath, grid_size, raw_image=None, difficulty="Normal"):
        self.__check_settings(grid_size, difficulty)
        image = self.decode_image(filepath) if raw_image is None else raw_image
        self.load_array(image, grid_size, difficulty)

    def load_array(self, image, grid_size, difficulty="Normal", scramble=True):
        """Start a round from an image already in memory."""
        self.__check_settings(grid_size, difficulty)
        if image is None or image.size == 0:
            raise ValueError("Invalid image file. Please choose a valid JPG, PNG, or BMP file.")

        prepared = self.__processor.prepare(image, grid_size)
        pieces = ImageProcessor.split(prepared, grid_size)
        tiles = [GridTile(i, piece, grid_size) for i, piece in enumerate(pieces)]

        self.__grid_size = grid_size
        self.__difficulty = difficulty
        self.__original = prepared
        self.__board = PuzzleBoard(tiles, grid_size, self.__rng)
        self.__game = PuzzleGame(self.__board)
        self.__scramble = []
        if scramble:
            self.__scramble = self.__generator.generate(grid_size, difficulty)
            for transformation in self.__scramble:
                transformation.apply(self)
        self.__board.reset()            # recount after scrambling
        self.clear_history()

    def restart(self):
        """Put the same scramble back and clear the player's progress."""
        if self.__board is None or not self.__scramble:
            return False
        self.__board.solve()
        for transformation in self.__scramble:
            transformation.apply(self)
        self.__board.reset()
        self.__game.reset_selection()
        self.clear_history()
        return True

    # ------------------------------------------------------------------ #
    # Used by the Transformation classes (scramble, undo, redo)
    # ------------------------------------------------------------------ #
    def tile_at(self, position):
        return self.__board.tile_at(position)

    def swap_positions(self, first, second):
        self.__board.swap_positions(first, second, count_move=False)

    # ------------------------------------------------------------------ #
    # Player moves (go through PuzzleGame, recorded for undo/redo)
    # ------------------------------------------------------------------ #
    def left_click(self, r, c):
        """Select / deselect / swap. Returns PuzzleGame's result string."""
        before = self.__game.selected_position
        result = self.__game.left_click(self.__to_index(r, c))
        if result == "swapped":
            self.__record(SwapTransformation(before, self.__to_index(r, c)))
        return result

    def swap_tiles(self, p1, p2):
        if p1 == p2:
            return
        move = SwapTransformation(self.__to_index(*p1), self.__to_index(*p2))
        move.apply(self)
        self.__record(move)

    def rotate_tile(self, r, c):
        position = self.__to_index(r, c)
        if self.__game.right_click(position):
            self.__record(RotateTransformation(position, 1))
        else:                   # board locked (solved) - still allow via history
            move = RotateTransformation(position, 1)
            move.apply(self)
            self.__record(move)

    def flip_tile(self, r, c):
        position = self.__to_index(r, c)
        if self.__game.shift_left_click(position):
            self.__record(FlipTransformation(position, FlipTransformation.HORIZONTAL))
        else:
            move = FlipTransformation(position, FlipTransformation.HORIZONTAL)
            move.apply(self)
            self.__record(move)

    def reset_selection(self):
        if self.__game is not None:
            self.__game.reset_selection()

    # ------------------------------------------------------------------ #
    # Undo / redo - polymorphism: every move knows how to undo itself
    # ------------------------------------------------------------------ #
    def undo(self):
        if not self.__undo_stack:
            return False
        move = self.__undo_stack.pop()
        move.undo(self)
        self.__redo_stack.append(move)
        self.__sync_board()
        return True

    def redo(self):
        if not self.__redo_stack:
            return False
        move = self.__redo_stack.pop()
        move.apply(self)
        self.__undo_stack.append(move)
        self.__sync_board()
        return True

    def clear_history(self):
        self.__undo_stack.clear()
        self.__redo_stack.clear()

    # ------------------------------------------------------------------ #
    # Checks, hints, solve, drawing
    # ------------------------------------------------------------------ #
    def is_tile_correct(self, r, c):
        return self.__board.is_position_correct(self.__to_index(r, c))

    def get_correct_positions(self):
        return [self.__to_rc(p) for p in range(len(self.__board))
                if self.__board.is_position_correct(p)]

    def get_incorrect_positions(self):
        return [self.__to_rc(p) for p in range(len(self.__board))
                if not self.__board.is_position_correct(p)]

    def get_hint_pair(self):
        hint = self.__board.use_hint()
        if hint is None:
            return None, None
        current, home = hint
        return self.__to_rc(current), self.__to_rc(home)

    def solve_all(self):
        self.__board.solve()
        self.reset_selection()
        self.clear_history()

    def reassemble_image(self):
        return ImageProcessor.reassemble([tile.render() for tile in self.__board.tiles],
                                         self.__grid_size)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def __record(self, move):
        self.__undo_stack.append(move)
        self.__redo_stack.clear()
        self.__sync_board()

    def __sync_board(self):
        """
        Rotations/flips from undo/redo change a Tile directly, so ask the
        board to re-check whether it is solved. Swapping two tiles and
        swapping them straight back (not counted as moves) makes PuzzleBoard
        recalculate without touching the move or hint counters.
        """
        if len(self.__board) > 1:
            self.__board.swap_positions(0, 1, count_move=False)
            self.__board.swap_positions(0, 1, count_move=False)

    def __to_index(self, r, c):
        return r * self.__grid_size + c

    def __to_rc(self, position):
        return divmod(position, self.__grid_size)

    @staticmethod
    def __check_settings(grid_size, difficulty):
        if (isinstance(grid_size, bool) or not isinstance(grid_size, int)
                or grid_size not in PuzzleEngine.GRID_SIZES):
            raise ValueError("Grid size must be 3, 4, or 5.")
        if difficulty not in TransformationGenerator.DIFFICULTIES:
            raise ValueError("Difficulty must be one of: "
                             f"{', '.join(TransformationGenerator.DIFFICULTIES)}.")


# Older name kept so existing code and tests still work
BuiltInPuzzleEngine = PuzzleEngine
