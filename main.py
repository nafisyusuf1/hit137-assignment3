"""
HIT137 Group Assignment 3 - Picture Puzzle
Run with:  python main.py
"""

import tkinter as tk

from app import PuzzleApp


def main():
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
