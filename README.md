# HIT137 Assignment 3 - Picture Puzzle

This project implements a picture-puzzle game where tiles can be swapped, rotated, and flipped to restore the original arrangement.

## Features

- 3x3, 4x4, and 5x5 puzzle boards
- Tile swapping with move tracking
- Rotation and flipping actions
- Hint system with a limit of three hints
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

- `game.py` - gameplay controller
- `puzzle_board.py` - board state, rules, and move logic
- `tests/` - unit tests for the game and board behavior
