# HIT137 Assignment 3 - Picture Puzzle

This project implements a picture-puzzle game where tiles can be swapped, rotated, and flipped to restore the original arrangement.

## Features

- 3x3, 4x4, and 5x5 puzzle boards
- Tile swapping with move tracking
- Rotation and flipping actions
- Grid-scaled random scrambling with swaps, rotations, and flips; each tile is targeted at most once
- Elapsed puzzle timer with completion time
- Persistent personal best completion times for 3x3, 4x4, and 5x5 puzzles
- Undo and redo for tile moves (also available with Ctrl+Z and Ctrl+Y)
- Restart the current puzzle with its original scramble (also available with Ctrl+R)
- Solve Puzzle asks for confirmation before revealing the solution and clearing the move count
- Keyboard gameplay: arrow keys move focus, Enter selects/swaps, R rotates, and F flips a tile
- Hint system with a limit of three hints
- Image loading validates the selected grid and reports missing or invalid image files
- Selected images can be previewed with zoom and fit controls before starting; cancelling preserves the current round
- Replacing an active puzzle requires confirmation before discarding progress
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
