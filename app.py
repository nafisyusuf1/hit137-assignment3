import os
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np

from best_times import BestTimes
from overlays import OverlayRenderer
from transformations import TransformationGenerator
from panels import (
    ControlPanel,
    StatusPanel,
    ImagePanel,
    InteractiveImagePanel,
    format_elapsed_time,
)


class Tile:
    """Encapsulates a single puzzle tile's image, home coordinates, and transformations."""
    def __init__(self, home_row: int, home_col: int, base_image: np.ndarray):
        self._home_pos = (home_row, home_col)
        self._base_image = base_image.copy()
        self._rotation = 0
        self._flipped_h = False
        self._flipped_v = False

    @property
    def home_pos(self) -> tuple:
        return self._home_pos

    def rotate_cw(self, times: int = 1):
        for _ in range(times % 4):
            if self._flipped_h != self._flipped_v:
                self._rotation = (self._rotation - 90) % 360
            else:
                self._rotation = (self._rotation + 90) % 360

    def rotate_clockwise(self, quarter_turns: int = 1):
        self.rotate_cw(quarter_turns)

    def flip_horizontal(self):
        self._flipped_h = not self._flipped_h

    def flip_vertical(self):
        self._flipped_v = not self._flipped_v

    def reset_orientation(self):
        self._rotation = 0
        self._flipped_h = False
        self._flipped_v = False

    def get_transformed_image(self) -> np.ndarray:
        img = self._base_image.copy()
        if self._rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif self._rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif self._rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if self._flipped_h:
            img = cv2.flip(img, 1)
        if self._flipped_v:
            img = cv2.flip(img, 0)
        return img

    def is_orientation_correct(self) -> bool:
        return np.array_equal(self.get_transformed_image(), self._base_image)


class BuiltInPuzzleEngine:
    """Handles OpenCV loading, scaling, cropping, random transformations, and puzzle state."""
    def __init__(self, display_max_size: int = 450):
        self._max_size = display_max_size
        self._grid_size = 3
        self._original_image = None
        self._tiles = []
        self._undo_stack = []
        self._redo_stack = []
        self._transformation_generator = TransformationGenerator()

    @property
    def original_image(self) -> np.ndarray:
        return self._original_image

    @property
    def grid_size(self) -> int:
        return self._grid_size

    def load_and_prepare(self, filepath: str, grid_size: int):
        if (
            isinstance(grid_size, bool)
            or not isinstance(grid_size, int)
            or grid_size not in (3, 4, 5)
        ):
            raise ValueError("Grid size must be 3, 4, or 5.")
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Image file not found: {filepath}")
        raw = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)
        if raw is None or raw.size == 0:
            raise ValueError("Invalid image file. Please choose a valid JPG, PNG, or BMP file.")

        prepared_image = self._resize_and_crop(raw, grid_size)
        self._grid_size = grid_size
        self._original_image = prepared_image
        self._slice_tiles()
        self._scramble_tiles()

    def _resize_and_crop(self, img: np.ndarray, grid_size: int) -> np.ndarray:
        h, w = img.shape[:2]
        scale = min(self._max_size / max(w, 1), self._max_size / max(h, 1))
        nw, nh = max(grid_size * 20, int(w * scale)), max(grid_size * 20, int(h * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        side = (min(nw, nh) // grid_size) * grid_size
        xs, ys = (nw - side) // 2, (nh - side) // 2
        return resized[ys:ys + side, xs:xs + side].copy()

    def _slice_tiles(self):
        h, w = self._original_image.shape[:2]
        th, tw = h // self._grid_size, w // self._grid_size
        self._tiles = [
            [Tile(r, c, self._original_image[r * th:(r + 1) * th, c * tw:(c + 1) * tw]) for c in range(self._grid_size)]
            for r in range(self._grid_size)
        ]

    def _scramble_tiles(self):
        for transformation in self._transformation_generator.generate(self._grid_size):
            transformation.apply(self)
        self.clear_history()

    def reassemble_image(self) -> np.ndarray:
        return np.vstack([
            np.hstack([self._tiles[r][c].get_transformed_image() for c in range(self._grid_size)])
            for r in range(self._grid_size)
        ])

    def swap_tiles(self, p1: tuple, p2: tuple):
        if p1 == p2:
            return
        self._swap_tiles(p1, p2)
        self._record_action(("swap", (p1, p2)))

    def _swap_tiles(self, p1: tuple, p2: tuple):
        r1, c1 = p1
        r2, c2 = p2
        self._tiles[r1][c1], self._tiles[r2][c2] = self._tiles[r2][c2], self._tiles[r1][c1]

    def swap_positions(self, first: int, second: int):
        first_row, first_col = divmod(first, self._grid_size)
        second_row, second_col = divmod(second, self._grid_size)
        self._swap_tiles((first_row, first_col), (second_row, second_col))

    def tile_at(self, position: int):
        row, col = divmod(position, self._grid_size)
        return self._tiles[row][col]

    def rotate_tile(self, r: int, c: int):
        self._tiles[r][c].rotate_cw(1)
        self._record_action(("rotate", ((r, c),)))

    def flip_tile(self, r: int, c: int):
        self._tiles[r][c].flip_horizontal()
        self._record_action(("flip", ((r, c),)))

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        action = self._undo_stack.pop()
        self._apply_action(action, reverse=True)
        self._redo_stack.append(action)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        action = self._redo_stack.pop()
        self._apply_action(action)
        self._undo_stack.append(action)
        return True

    def clear_history(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def _record_action(self, action):
        self._undo_stack.append(action)
        self._redo_stack.clear()

    def _apply_action(self, action, reverse: bool = False):
        action_type, positions = action
        if action_type == "swap":
            self._swap_tiles(*positions)
        elif action_type == "rotate":
            row, col = positions[0]
            self._tiles[row][col].rotate_cw(3 if reverse else 1)
        elif action_type == "flip":
            row, col = positions[0]
            self._tiles[row][col].flip_horizontal()
        else:
            raise ValueError(f"Unknown history action: {action_type}")

    def is_tile_correct(self, r: int, c: int) -> bool:
        t = self._tiles[r][c]
        return t.home_pos == (r, c) and t.is_orientation_correct()

    def get_correct_positions(self) -> list:
        return [(r, c) for r in range(self._grid_size) for c in range(self._grid_size) if self.is_tile_correct(r, c)]

    def get_incorrect_positions(self) -> list:
        return [(r, c) for r in range(self._grid_size) for c in range(self._grid_size) if not self.is_tile_correct(r, c)]

    def get_hint_pair(self) -> tuple:
        inc = self.get_incorrect_positions()
        if not inc:
            return None, None
        curr = random.choice(inc)
        return curr, self._tiles[curr[0]][curr[1]].home_pos

    def solve_all(self):
        solved = [[None for _ in range(self._grid_size)] for _ in range(self._grid_size)]
        for r in range(self._grid_size):
            for c in range(self._grid_size):
                t = self._tiles[r][c]
                t.reset_orientation()
                hr, hc = t.home_pos
                solved[hr][hc] = t
        self._tiles = solved
        self.clear_history()


class PuzzleApp:
    """Main Tkinter GUI Controller."""
    MAX_HINTS = 3

    def __init__(self, root: tk.Tk):
        self._root = root
        self._root.title("Puzzle Studio - Match the Picture")
        self._root.resizable(False, False)
        self._root.geometry("980x700")
        self._root.minsize(960, 640)
        self._root.configure(bg="#f6faff")
        self._configure_theme()

        self._engine = BuiltInPuzzleEngine(display_max_size=450)
        self._renderer = OverlayRenderer()
        self._best_times = BestTimes()
        self._moves = 0
        self._hints_left = self.MAX_HINTS
        self._selected_pos = None
        self._hint_curr = None
        self._hint_home = None
        self._active = False
        self._timer_started_at = None
        self._elapsed_seconds = 0.0
        self._build_ui()
        self._root.bind("<Control-z>", lambda _event: self._undo())
        self._root.bind("<Control-y>", lambda _event: self._redo())
        self._root.after(250, self._update_timer)

    def _configure_theme(self):
        style = ttk.Style(self._root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Panel.TFrame", background="#f6f8fc")
        style.configure("Heading.TLabel", background="#f6f8fc", foreground="#0f172a", font=("Segoe UI", 11, "bold"))
        style.configure("FieldLabel.TLabel", background="#f6f8fc", foreground="#334155", font=("Segoe UI", 10, "bold"))
        style.configure("Info.TLabel", background="#f6f8fc", foreground="#475569", font=("Segoe UI", 9))

        style.configure("Primary.TButton", background="#2563eb", foreground="white", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#cbd5e1")], foreground=[("disabled", "#475569")])

        style.configure("Secondary.TButton", background="#e2e8f0", foreground="#0f172a", padding=(9, 7), font=("Segoe UI", 10, "bold"))
        style.map("Secondary.TButton", background=[("active", "#cbd5e1"), ("disabled", "#e2e8f0")], foreground=[("disabled", "#64748b")])

        style.configure("Warning.TButton", background="#f59e0b", foreground="#111827", padding=(9, 7), font=("Segoe UI", 10, "bold"))
        style.map("Warning.TButton", background=[("active", "#d97706"), ("disabled", "#fcd34d")], foreground=[("disabled", "#78350f")])

        style.configure("Input.TCombobox", fieldbackground="#ffffff", background="#ffffff")
        style.configure("Horizontal.TProgressbar", troughcolor="#e2e8f0", background="#16a34a", bordercolor="#e2e8f0", lightcolor="#16a34a", darkcolor="#16a34a")

    def _build_ui(self):
        self._ctrl = ControlPanel(
            self._root, self._load_image, self._grid_changed, self._use_hint,
            self._solve, self._undo, self._redo
        )
        self._ctrl.pack(fill=tk.X)
        ttk.Separator(self._root, orient=tk.HORIZONTAL, style="Horizontal.TSeparator").pack(fill=tk.X, padx=6)
        self._status = StatusPanel(self._root)
        self._status.pack(fill=tk.X)
        ttk.Separator(self._root, orient=tk.HORIZONTAL, style="Horizontal.TSeparator").pack(fill=tk.X, padx=6)

        body = ttk.Frame(self._root, padding=10, style="Panel.TFrame")
        body.pack(fill=tk.BOTH, expand=True)
        self._orig_panel = ImagePanel(body, "Original Image (Reference Only)", 460)
        self._orig_panel.pack(side=tk.LEFT, padx=(0, 10))
        self._trans_panel = InteractiveImagePanel(
            body, "Transformed Puzzle (Click Tiles to Restore)", 460,
            on_left_click=self._left_click, on_right_click=self._right_click, on_shift_left_click=self._shift_left_click
        )
        self._trans_panel.pack(side=tk.LEFT)

    def _grid_changed(self, size: int):
        self._status.set_message(f"Grid size set to {size}x{size}. Click 'Load Image' to start.", "#334155")

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.JPG *.JPEG *.PNG *.BMP"), ("All Files", "*.*")]
        )
        if not path:
            return
        gsize = self._ctrl.get_grid_size()
        try:
            self._engine.load_and_prepare(path, gsize)
        except (OSError, ValueError, cv2.error) as e:
            messagebox.showerror("Image Load Error", str(e))
            return

        self._moves = 0
        self._hints_left = self.MAX_HINTS
        self._selected_pos = None
        self._hint_curr = None
        self._hint_home = None
        self._active = True
        self._elapsed_seconds = 0.0
        self._timer_started_at = time.monotonic()
        self._status.set_elapsed_time(0)
        self._refresh_best_time(gsize)
        self._trans_panel.set_grid_size(gsize)
        self._trans_panel.set_input_locked(False)
        self._ctrl.update_hint_button(self._hints_left, True)
        self._ctrl.set_solve_enabled(True)
        self._update_history_buttons()
        self._status.set_message(f"Loaded {os.path.basename(path)} ({gsize}x{gsize}). Restore the picture!", "#1d4ed8")
        self._refresh()

    def _clear_hint(self):
        self._hint_curr = None
        self._hint_home = None

    def _left_click(self, r: int, c: int):
        if not self._active:
            return
        if self._selected_pos is None:
            self._selected_pos = (r, c)
            self._status.set_message(f"Tile ({r + 1}, {c + 1}) selected. Click another tile to swap.", "#0f172a")
        elif self._selected_pos == (r, c):
            self._selected_pos = None
            self._status.set_message("Selection cleared.", "#334155")
        else:
            self._engine.swap_tiles(self._selected_pos, (r, c))
            self._selected_pos = None
            self._moves += 1
            self._clear_hint()
            self._update_history_buttons()
            self._status.set_message("Tiles swapped!", "#0f172a")
        self._refresh()
        self._check_win()

    def _right_click(self, r: int, c: int):
        if not self._active:
            return
        self._engine.rotate_tile(r, c)
        self._moves += 1
        self._clear_hint()
        self._update_history_buttons()
        self._status.set_message(f"Rotated tile ({r + 1}, {c + 1}) 90° clockwise.", "#0f172a")
        self._refresh()
        self._check_win()

    def _shift_left_click(self, r: int, c: int):
        if not self._active:
            return
        self._engine.flip_tile(r, c)
        self._moves += 1
        self._clear_hint()
        self._update_history_buttons()
        self._status.set_message(f"Flipped tile ({r + 1}, {c + 1}) horizontally.", "#0f172a")
        self._refresh()
        self._check_win()

    def _use_hint(self):
        if not self._active or self._hints_left <= 0:
            return
        curr, home = self._engine.get_hint_pair()
        if curr is None:
            return
        self._hint_curr, self._hint_home = curr, home
        self._hints_left -= 1
        self._ctrl.update_hint_button(self._hints_left, self._hints_left > 0)
        self._status.set_message(f"Hint: Tile ({curr[0]+1},{curr[1]+1}) belongs at ({home[0]+1},{home[1]+1}).", "#1d4ed8")
        self._refresh()

    def _solve(self):
        if not self._active:
            return
        elapsed = self._stop_timer()
        self._engine.solve_all()
        self._moves = 0
        self._selected_pos = None
        self._clear_hint()
        self._active = False
        self._trans_panel.set_input_locked(True)
        self._update_history_buttons()
        self._ctrl.update_hint_button(self._hints_left, False)
        self._ctrl.set_solve_enabled(False)
        self._refresh()
        self._status.set_message(
            f"Puzzle solved in {format_elapsed_time(elapsed)}! Moves and score cleared. "
            "Load a new image to play again.",
            "#15803d",
        )

    def _undo(self):
        if not self._engine.undo():
            return
        if not self._active:
            self._timer_started_at = time.monotonic()
            self._active = True
        self._moves = max(0, self._moves - 1)
        self._selected_pos = None
        self._clear_hint()
        self._trans_panel.set_input_locked(False)
        self._ctrl.update_hint_button(self._hints_left, self._hints_left > 0)
        self._ctrl.set_solve_enabled(True)
        self._update_history_buttons()
        self._status.set_message("Last move undone.", "#334155")
        self._refresh()

    def _redo(self):
        if not self._engine.redo():
            return
        self._moves += 1
        self._selected_pos = None
        self._clear_hint()
        self._update_history_buttons()
        self._status.set_message("Move redone.", "#334155")
        self._refresh()
        self._check_win()

    def _update_history_buttons(self):
        self._ctrl.set_history_enabled(self._engine.can_undo, self._engine.can_redo)

    def _current_elapsed_time(self) -> float:
        if self._timer_started_at is None:
            return self._elapsed_seconds
        return self._elapsed_seconds + time.monotonic() - self._timer_started_at

    def _stop_timer(self) -> float:
        self._elapsed_seconds = self._current_elapsed_time()
        self._timer_started_at = None
        self._status.set_elapsed_time(self._elapsed_seconds)
        return self._elapsed_seconds

    def _update_timer(self):
        if self._active:
            self._status.set_elapsed_time(self._current_elapsed_time())
        self._root.after(250, self._update_timer)

    def _refresh(self):
        gs = self._engine.grid_size
        orig = self._renderer.render_original(self._engine.original_image, gs, self._hint_home)
        trans = self._renderer.render_transformed(
            self._engine.reassemble_image(), gs, self._selected_pos,
            self._engine.get_correct_positions(), self._hint_curr
        )
        self._orig_panel.display_image(orig)
        self._trans_panel.display_image(trans)
        incorrect = self._engine.get_incorrect_positions()
        correct_count = gs * gs - len(incorrect)
        self._status.update_stats(self._moves, len(incorrect), correct_count, gs * gs)

    def _check_win(self):
        if self._active and len(self._engine.get_incorrect_positions()) == 0:
            elapsed = self._stop_timer()
            self._active = False
            self._selected_pos = None
            self._clear_hint()
            self._trans_panel.set_input_locked(True)
            self._ctrl.set_solve_enabled(False)
            self._ctrl.update_hint_button(self._hints_left, False)
            self._ctrl.set_solve_enabled(False)
            self._refresh()
            new_record = False
            try:
                new_record, best_time = self._best_times.record(
                    self._engine.grid_size, elapsed
                )
                self._status.set_best_time(self._engine.grid_size, best_time)
            except (OSError, ValueError) as error:
                messagebox.showerror("Best Time Error", str(error))
            elapsed_text = format_elapsed_time(elapsed)
            record_text = " New personal best!" if new_record else ""
            self._status.set_message(
                f"Congratulations! Completed in {self._moves} moves and "
                f"{elapsed_text}!{record_text}",
                "#15803d",
            )
            messagebox.showinfo(
                "Puzzle Complete!",
                f"You restored the image in {self._moves} moves and "
                f"{elapsed_text}!{record_text}",
            )

    def _refresh_best_time(self, grid_size: int):
        try:
            best_time = self._best_times.best_for(grid_size)
        except (OSError, ValueError) as error:
            self._status.set_best_time(grid_size, None)
            messagebox.showerror("Best Time Error", str(error))
            return
        self._status.set_best_time(grid_size, best_time)


if __name__ == "__main__":
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()
