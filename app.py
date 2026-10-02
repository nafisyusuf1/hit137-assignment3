import os
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np

from best_times import BestTimes
from overlays import OverlayRenderer
from puzzle_engine import BuiltInPuzzleEngine, PuzzleEngine
from panels import (
    ControlPanel,
    StatusPanel,
    ImagePanel,
    InteractiveImagePanel,
    ImagePreviewDialog,
    format_elapsed_time,
)


def move_grid_focus(
    position: tuple[int, int],
    row_delta: int,
    col_delta: int,
    grid_size: int,
) -> tuple[int, int]:
    """Move keyboard focus by one step while keeping it inside the puzzle."""
    row, col = position
    return (
        min(max(row + row_delta, 0), grid_size - 1),
        min(max(col + col_delta, 0), grid_size - 1),
    )


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

        self._engine = PuzzleEngine(display_max_size=450)
        self._renderer = OverlayRenderer()
        self._best_times = BestTimes()
        self._moves = 0
        self._hints_left = self.MAX_HINTS
        self._selected_pos = None
        self._engine.reset_selection()
        self._focused_pos = (0, 0)
        self._hint_curr = None
        self._hint_home = None
        self._active = False
        self._timer_started_at = None
        self._elapsed_seconds = 0.0
        self._build_ui()
        self._root.bind("<Control-z>", lambda _event: self._undo())
        self._root.bind("<Control-y>", lambda _event: self._redo())
        self._root.bind("<Control-r>", lambda _event: self._keyboard_restart())
        self._root.bind("<Control-R>", lambda _event: self._keyboard_restart())
        self._root.bind("<Up>", lambda _event: self._move_keyboard_focus(-1, 0))
        self._root.bind("<Down>", lambda _event: self._move_keyboard_focus(1, 0))
        self._root.bind("<Left>", lambda _event: self._move_keyboard_focus(0, -1))
        self._root.bind("<Right>", lambda _event: self._move_keyboard_focus(0, 1))
        self._root.bind("<Return>", lambda _event: self._keyboard_select())
        self._root.bind("<space>", lambda _event: self._keyboard_select())
        self._root.bind("<r>", lambda _event: self._keyboard_rotate())
        self._root.bind("<R>", lambda _event: self._keyboard_rotate())
        self._root.bind("<f>", lambda _event: self._keyboard_flip())
        self._root.bind("<F>", lambda _event: self._keyboard_flip())
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
            self._solve, self._undo, self._redo, self._restart
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
        difficulty = self._ctrl.get_difficulty()
        prefix = "Next puzzle settings" if self._active else "Settings"
        self._status.set_message(
            f"{prefix}: {size}x{size}, {difficulty}. Load an image to start.",
            "#334155",
        )

    def _load_image(self):
        if self._active and not messagebox.askyesno(
            "Replace Current Puzzle",
            "Loading a new image will replace the current puzzle and discard "
            "its progress. Continue?",
            parent=self._root,
        ):
            return
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.JPG *.JPEG *.PNG *.BMP"), ("All Files", "*.*")]
        )
        if not path:
            return
        gsize = self._ctrl.get_grid_size()
        difficulty = self._ctrl.get_difficulty()
        try:
            raw_image = self._engine.decode_image(path)
            if not self._confirm_image_preview(path, raw_image, gsize, difficulty):
                return
        except (OSError, ValueError, cv2.error) as e:
            messagebox.showerror("Image Preview Error", str(e))
            return
        try:
            self._engine.load_and_prepare(
                path,
                gsize,
                raw_image=raw_image,
                difficulty=difficulty,
            )
        except (OSError, ValueError, cv2.error) as e:
            messagebox.showerror("Image Load Error", str(e))
            return

        self._moves = 0
        self._hints_left = self.MAX_HINTS
        self._selected_pos = None
        self._engine.reset_selection()
        self._focused_pos = (0, 0)
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
        self._ctrl.set_restart_enabled(True)
        self._update_history_buttons()
        self._status.set_message(
            f"Loaded {os.path.basename(path)} ({gsize}x{gsize}, {difficulty}). "
            "Restore the picture!",
            "#1d4ed8",
        )
        self._refresh()

    def _confirm_image_preview(
        self,
        filepath: str,
        raw_image: np.ndarray,
        grid_size: int,
        difficulty: str,
    ) -> bool:
        return ImagePreviewDialog(
            self._root,
            filepath,
            self._engine.prepare_preview(raw_image, grid_size),
            grid_size,
            difficulty,
        ).show()

    def _clear_hint(self):
        self._hint_curr = None
        self._hint_home = None

    def _left_click(self, r: int, c: int):
        if not self._active:
            return
        result = self._engine.left_click(r, c)
        self._selected_pos = self._engine.selected_pos
        if result == "selected":
            self._status.set_message(f"Tile ({r + 1}, {c + 1}) selected. Click another tile to swap.", "#0f172a")
        elif result == "deselected":
            self._status.set_message("Selection cleared.", "#334155")
        elif result == "swapped":
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

    def _move_keyboard_focus(self, row_delta: int, col_delta: int):
        if not self._active:
            return "break"
        self._focused_pos = move_grid_focus(
            self._focused_pos,
            row_delta,
            col_delta,
            self._engine.grid_size,
        )
        self._refresh()
        return "break"

    def _keyboard_select(self):
        if self._active:
            self._left_click(*self._focused_pos)
        return "break"

    def _keyboard_rotate(self):
        if self._active:
            self._right_click(*self._focused_pos)
        return "break"

    def _keyboard_flip(self):
        if self._active:
            self._shift_left_click(*self._focused_pos)
        return "break"

    def _keyboard_restart(self):
        self._restart()
        return "break"

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
        confirmed = messagebox.askyesno(
            "Solve Puzzle",
            "Are you sure you want to reveal the solution? "
            "This will clear your move count and will not record a best time.",
            parent=self._root,
        )
        if not confirmed:
            return
        elapsed = self._stop_timer()
        self._engine.solve_all()
        self._moves = 0
        self._selected_pos = None
        self._engine.reset_selection()
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

    def _restart(self):
        if not self._engine.restart():
            return
        self._moves = 0
        self._hints_left = self.MAX_HINTS
        self._selected_pos = None
        self._engine.reset_selection()
        self._focused_pos = (0, 0)
        self._clear_hint()
        self._active = True
        self._elapsed_seconds = 0.0
        self._timer_started_at = time.monotonic()
        self._status.set_elapsed_time(0)
        self._trans_panel.set_input_locked(False)
        self._ctrl.update_hint_button(self._hints_left, True)
        self._ctrl.set_solve_enabled(True)
        self._ctrl.set_restart_enabled(True)
        self._update_history_buttons()
        self._status.set_message("Puzzle restarted. Restore the picture!", "#1d4ed8")
        self._refresh()

    def _undo(self):
        if not self._engine.undo():
            return
        if not self._active:
            self._timer_started_at = time.monotonic()
            self._active = True
        self._moves = max(0, self._moves - 1)
        self._selected_pos = None
        self._engine.reset_selection()
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
        self._engine.reset_selection()
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
            self._engine.get_correct_positions(), self._hint_curr,
            focused_pos=self._focused_pos if self._active else None,
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
            self._engine.reset_selection()
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
