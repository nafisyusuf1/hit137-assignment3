# HIT137 Assignment 3 - Picture Puzzle

This project implements a picture-puzzle game where tiles can be swapped, rotated, and flipped to restore the original arrangement.

## Features

- 3x3, 4x4, and 5x5 puzzle boards
- Tile swapping with move tracking
- Rotation and flipping actions
- Elapsed puzzle timer with completion time
- Undo and redo for tile moves (also available with Ctrl+Z and Ctrl+Y)
- Hint system with a limit of three hints
- Image loading validates the selected grid and reports missing or invalid image files
- Solve/reset handling and solved-state lockout
- Unit tests covering the board and game logic

## Run the game

```bash
python main.py
```

## Run the tests

```bash
python -m unittest discover -s tests -q
```

## Project files

- `app.py` - Tkinter application and picture-puzzle engine
- `panels.py` - application controls and image panels
- `tests/` - unit tests for the game and board behavior
