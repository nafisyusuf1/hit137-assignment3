# HIT137 Assignment 3 – Picture Puzzle

A desktop picture-puzzle game built with **Tkinter** and **OpenCV**. A loaded image is cut into a grid of tiles, which are then randomly swapped, rotated and flipped. The player restores the picture by clicking the tiles.

## Team

| Member | GitHub | Main contribution |
|---|---|---|
| Nafis Yusuf | nafisyusuf1 | Image processing (`image_processor.py`), `Tile` class, transformations and scrambler, `puzzle_engine.py` connecting all parts |
| Andrew | AndrewM14 | Game rules (`puzzle_board.py`, `game.py`) and their unit tests |
| Hashir Ahmed | ahmedhashir074-a11y | Tkinter GUI (`app.py`, `panels.py`), overlays, best times, undo/redo, keyboard controls |

## How to run

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+ with Tkinter. The dependencies are OpenCV, NumPy and Pillow.

To run the unit tests:

```bash
python -m unittest discover tests
```

## How to play

1. Choose a **grid size** (3×3, 4×4 or 5×5). Leave Difficulty on **Normal** for the standard game.
2. Click **Load Image**, pick a JPG, PNG or BMP, then click **Start Puzzle** in the preview.
3. Restore the picture on the right. The original is shown on the left for reference.

| Action | Mouse | Keyboard |
|---|---|---|
| Select a tile / swap two tiles / deselect | Left-click | Arrow keys + Enter |
| Rotate 90° clockwise | Right-click | R |
| Flip horizontally | Shift + left-click | F |
| Undo / Redo | Undo / Redo buttons | Ctrl+Z / Ctrl+Y |
| Restart same puzzle | Restart button | Ctrl+R |

- A **green tick** marks every tile that is in the right place and the right way round.
- **Hint** circles one wrong tile in blue and circles its correct home on the original picture. You get 3 hints per image, and the circles disappear after the next move.
- **Solve Puzzle** restores the picture instantly and clears the moves and score.
- The counters show moves used, tiles still incorrect, progress, time and your best time.
- When every tile is correct, the player is notified and the puzzle locks until a new image is loaded.

## Project structure

| File | Classes | Responsibility |
|---|---|---|
| `main.py` | – | Starts the application |
| `app.py` | `PuzzleApp` | Main window: connects buttons, clicks and counters to the engine |
| `panels.py` | `BasePanel` → `ControlPanel`, `StatusPanel`, `ImagePanel` → `InteractiveImagePanel`; `ImagePreviewDialog` | Tkinter widgets, image display, click-to-tile mapping |
| `overlays.py` | `Overlay` → `GridOverlay`, `SelectionOverlay`, `FocusOverlay`, `TickOverlay`, `HintOverlay`; `OverlayRenderer` | OpenCV drawing of grid lines, selection, ticks and hint circles |
| `puzzle_engine.py` | `PuzzleEngine`, `GridTile` | Connects all the classes below so the GUI has one object to talk to |
| `image_processor.py` | `ImageProcessor`, `ImageLoadError` | OpenCV: load, resize, crop, split into tiles, reassemble |
| `tile.py` | `Tile` | One puzzle piece: home position plus rotation/flip state |
| `transformations.py` | `Transformation` → `SwapTransformation`, `RotateTransformation`, `FlipTransformation`; `TransformationGenerator` | Moves that can apply and undo themselves; random scramble |
| `puzzle_board.py` | `PuzzleBoard` | Tile order, correctness checks, hints, solve |
| `game.py` | `PuzzleGame` | Turns clicks into select / swap / rotate / flip, and locks input when solved |
| `best_times.py` | `BestTimes` | Saves the best completion time for each grid size |
| `tests/` | – | Unit tests |
| `outputs/` | – | Screenshots of the program running |

### How the parts work together

```
PuzzleApp (GUI) ──► PuzzleEngine ──► ImageProcessor   (load / prepare / split / reassemble)
      │                   ├────────► PuzzleBoard ◄── PuzzleGame   (rules + click handling)
      │                   │               └── GridTile (extends Tile)
      │                   └────────► TransformationGenerator ──► Swap / Rotate / Flip
      └──► Panels + OverlayRenderer ──► Overlay subclasses   (drawing)
```

## Object-oriented design

- **Encapsulation:** state is kept in private attributes and exposed through properties and methods. For example, `Tile` hides its pixels and orientation, and `PuzzleBoard` hides the tile list, move count and hint count.
- **Constructors:** every class sets up its state in `__init__`, and subclasses call `super().__init__()`.
- **Inheritance:**
  - `Transformation` → Swap / Rotate / Flip
  - `Overlay` → Grid / Selection / Focus / Tick / Hint
  - `BasePanel` → panels
  - `Tile` → `GridTile`
- **Polymorphism:**
  - Scrambling, undo and redo call `apply()` / `undo()` on any kind of transformation.
  - The renderer calls `draw()` on any kind of overlay.
- **Class interaction:** the GUI talks only to `PuzzleEngine`, which delegates to `ImageProcessor`, `PuzzleBoard`, `PuzzleGame` and the transformations.

## Image processing

- **Loading:** images are read with OpenCV (`np.fromfile` + `cv2.imdecode`, so folder names with spaces or non-English characters work). Bad files show an error message box instead of crashing.
- **Resizing:** the image is resized to fit the window while keeping its aspect ratio. It's then centre-cropped to a square whose side divides evenly by the grid size. Square tiles are needed so a rotated tile still fits in its slot.
- **Scrambling:** every load generates n × (n − 1) random transformations on Normal: **6** for 3×3, **12** for 4×4 and **20** for 5×5. There's always at least one swap, one rotation (90/180/270°) and one flip (horizontal or vertical), and no tile is targeted twice. Easy and Hard use fewer or more transformations.
- **Display:** tiles are reassembled into one image, and the overlays are drawn on top with OpenCV.
