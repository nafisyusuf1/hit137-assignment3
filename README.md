<<<<<<< HEAD
# HIT137 Assignment 3 – Picture Puzzle

A Tkinter + OpenCV desktop game. Load a picture, and it gets cut into a grid of tiles that are randomly swapped, rotated and flipped. Put the picture back together.

## How to run

```bash
pip install -r requirements.txt
python main.py
```

Needs Python 3.9+ with Tkinter (included with the normal Windows/macOS Python installers).

## How to play

1. Pick a grid size (3 × 3, 4 × 4 or 5 × 5).
2. Click **Load Image…** and choose a JPG, PNG or BMP file. There are some in `sample_images/`.
3. Fix the picture on the right-hand side:

| Action | What it does |
|---|---|
| Left-click a tile | Select it (orange border) |
| Left-click another tile | Swap the two tiles |
| Left-click the same tile | Deselect it |
| Right-click | Rotate 90° clockwise |
| Shift + left-click | Flip horizontally |

- A green tick shows a tile that's in the right place and the right way round.
- **Hint** puts a blue circle on one wrong tile and on the spot where it belongs in the original. You get 3 hints per image, and the circle disappears after your next move.
- **Solve** undoes everything and restores the picture straight away.
- Every swap, rotate or flip counts as 1 move. Once the picture is complete, the puzzle locks until you load a new image.

## Project structure

| File | Class(es) | Job |
|---|---|---|
| `main.py` | – | Starts the app |
| `app.py` | `PuzzleApp` | Main window, buttons, counters, message boxes |
| `panels.py` | `ImagePanel` → `OriginalPanel`, `PuzzlePanel` | The two image areas, mapping clicks to tiles |
| `game.py` | `PuzzleGame` | One round of play: turns clicks into moves |
| `puzzle_board.py` | `PuzzleBoard` | Tile grid, move counter, hints, win check, solve |
| `tile.py` | `Tile` | One tile and its orientation (rotation/flip) |
| `transformations.py` | `Transformation` → `SwapTransformation`, `RotateTransformation`, `FlipTransformation`; `TransformationGenerator` | Moves that can be applied and undone, plus random scrambling |
| `image_processor.py` | `ImageProcessor`, `ImageLoadError` | OpenCV load, resize, crop, split, reassemble |
| `overlays.py` | `Overlay` → `GridOverlay`, `TickOverlay`, `HintOverlay`, `SelectionOverlay` | Everything drawn on top of the images |
| `tests/test_puzzle.py` | – | Unit tests (`python -m unittest discover tests`) |
| `outputs/` | – | Screenshots of the program running |

## Where the OOP requirements are met

- **Encapsulation:** state is kept in private (`__name`) attributes and accessed only through properties and methods. For example, `Tile` keeps its original pixels and orientation private, and `PuzzleBoard` keeps the tile list, move count and hint count private.
- **Constructors:** every class sets up its state in `__init__`. Subclasses call `super().__init__()`.
- **Inheritance:** there are three hierarchies: `Transformation`, `Overlay` and `ImagePanel`. `PuzzleApp` also inherits from `tk.Tk`.
- **Polymorphism:**
  - `PuzzleBoard.solve()` calls `undo()` on a mixed list of swaps, rotates and flips.
  - Each panel draws a mixed list of overlays by calling `draw()` on each one.
  - The app calls `update_view()` on both panels without checking which kind each one is.
- **Class interaction:** `PuzzleApp` → `PuzzleGame` → `ImageProcessor` + `PuzzleBoard` → `Tile` / `Transformation`. The panels read the game's state and draw `Overlay` objects.

## Image processing details

- The image is resized so it fits the window without changing its aspect ratio. It's then centre-cropped to a square whose side divides exactly by the grid size. Tiles have to be square so a rotated tile still fits in its slot.
- Every load creates n × (n − 1) random transformations: 6 for 3 × 3, 12 for 4 × 4 and 20 for 5 × 5. There's always at least one swap, one rotation (90/180/270°) and one flip (horizontal or vertical), and no tile is targeted twice. All of them are applied at once.
- The tiles are joined back into one image with `np.hstack`/`np.vstack`, and the overlays are drawn with OpenCV.

## Error handling

- Cancelling the file dialog keeps the current game.
- Missing files, non-image files, corrupt images and tiny images all show an error message box.
- Clicks outside the picture are ignored, and so is input after the puzzle is finished.
- Any unexpected error is shown in a message box instead of crashing the app.
=======
# Assignment-3-HIT137-
>>>>>>> origin/main
