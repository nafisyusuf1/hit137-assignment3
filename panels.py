import tkinter as tk
from pathlib import Path
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk


def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time as MM:SS, or HH:MM:SS after an hour."""
    elapsed = max(0, int(seconds))
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def make_image_preview(image: np.ndarray, max_size: tuple[int, int] = (480, 360)) -> Image.Image:
    """Convert a BGR image into a proportionally scaled PIL preview."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    preview = Image.fromarray(rgb)
    preview.thumbnail(max_size, Image.Resampling.LANCZOS)
    return preview


class ImagePreviewDialog:
    """Modal preview that lets the user start or cancel loading an image."""

    def __init__(
        self,
        parent: tk.Misc,
        filepath: str,
        image: np.ndarray,
        grid_size: int,
    ) -> None:
        self._window = tk.Toplevel(parent)
        self._window.title("Preview Puzzle Image")
        self._window.transient(parent)
        self._window.resizable(False, False)
        self._accepted = False
        self._photo = ImageTk.PhotoImage(make_image_preview(image), master=self._window)

        content = ttk.Frame(self._window, padding=12)
        content.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            content,
            text=f"{Path(filepath).name}  |  {grid_size}x{grid_size} puzzle",
            style="Heading.TLabel",
        ).pack(pady=(0, 8))
        ttk.Label(content, image=self._photo).pack()
        ttk.Label(
            content,
            text="Start this puzzle with the selected image?",
            style="Info.TLabel",
        ).pack(pady=(8, 10))

        buttons = ttk.Frame(content, style="Panel.TFrame")
        buttons.pack(fill=tk.X)
        ttk.Button(
            buttons,
            text="Cancel",
            command=self._cancel,
            style="Secondary.TButton",
        ).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(
            buttons,
            text="Start Puzzle",
            command=self._accept,
            style="Primary.TButton",
        ).pack(side=tk.RIGHT)
        self._window.protocol("WM_DELETE_WINDOW", self._cancel)

    def show(self) -> bool:
        self._window.grab_set()
        self._window.wait_window()
        return self._accepted

    def _accept(self) -> None:
        self._accepted = True
        self._window.destroy()

    def _cancel(self) -> None:
        self._window.destroy()


class BasePanel(ttk.Frame):
    """Base class for UI panels demonstrating OOP Inheritance."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="Panel.TFrame")


class ControlPanel(BasePanel):
    """Toolbar with image, history, hint, and solve controls."""
    def __init__(
        self,
        parent,
        on_load,
        on_grid_change,
        on_hint,
        on_solve,
        on_undo,
        on_redo,
        on_restart,
    ):
        super().__init__(parent, padding=(12, 10))
        self._on_load = on_load
        self._on_grid_change = on_grid_change
        self._on_hint = on_hint
        self._on_solve = on_solve
        self._on_undo = on_undo
        self._on_redo = on_redo
        self._on_restart = on_restart
        self._grid_var = tk.StringVar(value="3x3")
        self._build_ui()

    def _build_ui(self):
        ttk.Button(self, text="Load Image", command=self._on_load, style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(self, text="Grid Size:", style="FieldLabel.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        self._combo = ttk.Combobox(self, textvariable=self._grid_var, values=["3x3", "4x4", "5x5"], state="readonly", width=6, style="Input.TCombobox")
        self._combo.pack(side=tk.LEFT, padx=(0, 16))
        self._combo.bind("<<ComboboxSelected>>", lambda _e: self._on_grid_change(self.get_grid_size()))

        self._undo_btn = ttk.Button(self, text="Undo", command=self._on_undo, state=tk.DISABLED, style="Secondary.TButton")
        self._undo_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._redo_btn = ttk.Button(self, text="Redo", command=self._on_redo, state=tk.DISABLED, style="Secondary.TButton")
        self._redo_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._restart_btn = ttk.Button(
            self,
            text="Restart",
            command=self._on_restart,
            state=tk.DISABLED,
            style="Secondary.TButton",
        )
        self._restart_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._hint_btn = ttk.Button(self, text="Hint (3 left)", command=self._on_hint, state=tk.DISABLED, style="Secondary.TButton")
        self._hint_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._solve_btn = ttk.Button(self, text="Solve Puzzle", command=self._on_solve, state=tk.DISABLED, style="Warning.TButton")
        self._solve_btn.pack(side=tk.LEFT, padx=(0, 8))

        legend = "Arrows: Move | Enter: Select/Swap | R: Rotate | F: Flip | Ctrl+Z/Y: Undo/Redo"
        ttk.Label(self, text=legend, style="Info.TLabel", wraplength=450, justify=tk.RIGHT).pack(side=tk.RIGHT)

    def set_history_enabled(self, can_undo: bool, can_redo: bool):
        self._undo_btn.config(state=tk.NORMAL if can_undo else tk.DISABLED)
        self._redo_btn.config(state=tk.NORMAL if can_redo else tk.DISABLED)

    def get_grid_size(self) -> int:
        return int(self._grid_var.get().split("x")[0])

    def update_hint_button(self, hints_remaining: int, enabled: bool = True):
        self._hint_btn.config(text=f"Hint ({hints_remaining} left)")
        self._hint_btn.config(state=tk.NORMAL if (hints_remaining > 0 and enabled) else tk.DISABLED)

    def set_solve_enabled(self, enabled: bool):
        self._solve_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_restart_enabled(self, enabled: bool):
        self._restart_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)


class StatusPanel(BasePanel):
    """Displays moves, tile progress, elapsed time, and status messages."""
    def __init__(self, parent):
        super().__init__(parent, padding=(12, 6))
        self._moves_var = tk.StringVar(value="Moves Used: 0")
        self._inc_var = tk.StringVar(value="Tiles Incorrect: 0")
        self._progress_var = tk.StringVar(value="0%")
        self._time_var = tk.StringVar(value="Time: 00:00")
        self._best_time_var = tk.StringVar(value="Best: --")
        self._msg_var = tk.StringVar(value="Choose grid size and click 'Load Image' to start.")
        self._build_ui()

    def _build_ui(self):
        stats = ttk.Frame(self, style="Panel.TFrame")
        stats.pack(fill=tk.X)
        ttk.Label(stats, textvariable=self._moves_var, font=("Segoe UI", 10, "bold"), foreground="#1d4ed8", background="#f7f9fc").pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(stats, textvariable=self._inc_var, font=("Segoe UI", 10, "bold"), foreground="#b91c1c", background="#f7f9fc").pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(stats, text="Progress", font=("Segoe UI", 9, "bold"), foreground="#334155", background="#f7f9fc").pack(side=tk.LEFT, padx=(0, 6))
        self._progress = ttk.Progressbar(stats, maximum=100, length=110, mode="determinate")
        self._progress.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(stats, textvariable=self._progress_var, font=("Segoe UI", 9, "bold"), foreground="#15803d", background="#f7f9fc", width=4).pack(side=tk.LEFT)
        ttk.Label(stats, textvariable=self._time_var, font=("Segoe UI", 10, "bold"), foreground="#334155", background="#f7f9fc").pack(side=tk.LEFT, padx=(16, 0))
        ttk.Label(stats, textvariable=self._best_time_var, font=("Segoe UI", 10, "bold"), foreground="#7c3aed", background="#f7f9fc").pack(side=tk.LEFT, padx=(12, 0))
        self._msg_lbl = ttk.Label(self, textvariable=self._msg_var, font=("Segoe UI", 9), foreground="#1f2937", background="#f7f9fc", wraplength=900, justify=tk.LEFT)
        self._msg_lbl.pack(fill=tk.X, pady=(4, 0))

    def update_stats(self, moves: int, incorrect_count: int, correct_count: int, total_tiles: int):
        self._moves_var.set(f"Moves Used: {moves}")
        self._inc_var.set(f"Tiles Incorrect: {incorrect_count}")
        progress = round(correct_count / total_tiles * 100) if total_tiles else 0
        self._progress.configure(value=progress)
        self._progress_var.set(f"{progress}%")

    def set_elapsed_time(self, seconds: float):
        self._time_var.set(f"Time: {format_elapsed_time(seconds)}")

    def set_best_time(self, grid_size: int, seconds: float | None):
        value = format_elapsed_time(seconds) if seconds is not None else "--"
        self._best_time_var.set(f"Best {grid_size}x{grid_size}: {value}")

    def set_message(self, message: str, color: str = "#374151"):
        self._msg_var.set(message)
        self._msg_lbl.config(foreground=color)


class ImagePanel(BasePanel):
    """Renders an OpenCV image on a Tkinter Canvas (non-interactive reference panel)."""
    def __init__(self, parent, title: str, canvas_size: int = 460):
        super().__init__(parent, padding=8)
        self._title = title
        self._canvas_size = canvas_size
        self._photo = None
        self._img_bounds = None
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text=self._title, font=("Segoe UI", 11, "bold"), style="Heading.TLabel").pack(pady=(0, 6))
        self._canvas = tk.Canvas(self, width=self._canvas_size, height=self._canvas_size, bg="#e2e8f0", highlightthickness=2, highlightbackground="#cbd5e1", relief="solid", bd=1)
        self._canvas.pack()
        self._draw_placeholder()

    def _draw_placeholder(self):
        self._canvas.delete("all")
        c = self._canvas_size // 2
        self._canvas.create_rectangle(12, 12, self._canvas_size - 12, self._canvas_size - 12, fill="#eef2ff", outline="#c4b5fd", width=2)
        self._canvas.create_text(c, c, text="No Image Loaded", fill="#64748b", font=("Segoe UI", 13, "bold"))
        self._img_bounds = None

    def display_image(self, bgr_image: np.ndarray):
        if bgr_image is None:
            self._draw_placeholder()
            return
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        self._photo = ImageTk.PhotoImage(image=pil_img)
        w, h = pil_img.size
        x_off = (self._canvas_size - w) // 2
        y_off = (self._canvas_size - h) // 2
        self._img_bounds = (x_off, y_off, w, h)
        self._canvas.delete("all")
        self._canvas.create_image(x_off, y_off, anchor=tk.NW, image=self._photo)


class InteractiveImagePanel(ImagePanel):
    """Subclasses ImagePanel to handle mouse clicks on the transformed puzzle image."""
    def __init__(self, parent, title: str, canvas_size: int = 460, on_left_click=None, on_right_click=None, on_shift_left_click=None):
        super().__init__(parent, title, canvas_size)
        self._grid_size = 3
        self._locked = True
        self._on_left = on_left_click
        self._on_right = on_right_click
        self._on_shift_left = on_shift_left_click

        self._canvas.bind("<Button-1>", self._handle_left)
        self._canvas.bind("<Shift-Button-1>", self._handle_shift_left)
        self._canvas.bind("<Button-3>", self._handle_right)
        self._canvas.bind("<Button-2>", self._handle_right)

    def set_grid_size(self, grid_size: int):
        self._grid_size = grid_size

    def set_input_locked(self, locked: bool):
        self._locked = locked

    def _get_tile(self, event):
        if self._locked or self._img_bounds is None:
            return None
        x_off, y_off, w, h = self._img_bounds
        rx, ry = event.x - x_off, event.y - y_off
        if rx < 0 or ry < 0 or rx >= w or ry >= h:
            return None
        tw, th = w // self._grid_size, h // self._grid_size
        return min(int(ry // th), self._grid_size - 1), min(int(rx // tw), self._grid_size - 1)

    def _handle_left(self, event):
        if event.state & 0x0001:
            return self._handle_shift_left(event)
        pos = self._get_tile(event)
        if pos and self._on_left:
            self._on_left(*pos)

    def _handle_shift_left(self, event):
        pos = self._get_tile(event)
        if pos and self._on_shift_left:
            self._on_shift_left(*pos)
        return "break"

    def _handle_right(self, event):
        pos = self._get_tile(event)
        if pos and self._on_right:
            self._on_right(*pos)
