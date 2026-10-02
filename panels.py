import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk


class BasePanel(ttk.Frame):
    """Base class for UI panels demonstrating OOP Inheritance."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="Panel.TFrame")


class ControlPanel(BasePanel):
    """Toolbar with Load Image, Grid Size selector, Hint, and Solve controls."""
    def __init__(self, parent, on_load, on_grid_change, on_hint, on_solve):
        super().__init__(parent, padding=(12, 10))
        self._on_load = on_load
        self._on_grid_change = on_grid_change
        self._on_hint = on_hint
        self._on_solve = on_solve
        self._grid_var = tk.StringVar(value="3x3")
        self._build_ui()

    def _build_ui(self):
        ttk.Button(self, text="Load Image", command=self._on_load, style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(self, text="Grid Size:", style="FieldLabel.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        self._combo = ttk.Combobox(self, textvariable=self._grid_var, values=["3x3", "4x4", "5x5"], state="readonly", width=6, style="Input.TCombobox")
        self._combo.pack(side=tk.LEFT, padx=(0, 16))
        self._combo.bind("<<ComboboxSelected>>", lambda _e: self._on_grid_change(self.get_grid_size()))

        self._hint_btn = ttk.Button(self, text="Hint (3 left)", command=self._on_hint, state=tk.DISABLED, style="Secondary.TButton")
        self._hint_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._solve_btn = ttk.Button(self, text="Solve Puzzle", command=self._on_solve, state=tk.DISABLED, style="Warning.TButton")
        self._solve_btn.pack(side=tk.LEFT, padx=(0, 8))

        legend = "Left-Click: Select/Swap | Right-Click: Rotate 90° | Shift+Left-Click: Flip Horizontal"
        ttk.Label(self, text=legend, style="Info.TLabel", wraplength=420, justify=tk.RIGHT).pack(side=tk.RIGHT)

    def get_grid_size(self) -> int:
        return int(self._grid_var.get().split("x")[0])

    def update_hint_button(self, hints_remaining: int, enabled: bool = True):
        self._hint_btn.config(text=f"Hint ({hints_remaining} left)")
        self._hint_btn.config(state=tk.NORMAL if (hints_remaining > 0 and enabled) else tk.DISABLED)

    def set_solve_enabled(self, enabled: bool):
        self._solve_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)


class StatusPanel(BasePanel):
    """Displays Moves Used, Tiles Incorrect, and status messages."""
    def __init__(self, parent):
        super().__init__(parent, padding=(12, 8))
        self._moves_var = tk.StringVar(value="Moves Used: 0")
        self._inc_var = tk.StringVar(value="Tiles Incorrect: 0")
        self._msg_var = tk.StringVar(value="Choose grid size and click 'Load Image' to start.")
        self._build_ui()

    def _build_ui(self):
        left = ttk.Frame(self, style="Panel.TFrame")
        left.pack(side=tk.LEFT)
        ttk.Label(left, textvariable=self._moves_var, font=("Segoe UI", 11, "bold"), foreground="#1d4ed8", background="#f7f9fc").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(left, textvariable=self._inc_var, font=("Segoe UI", 11, "bold"), foreground="#b91c1c", background="#f7f9fc").pack(side=tk.LEFT, padx=(0, 20))
        self._msg_lbl = ttk.Label(self, textvariable=self._msg_var, font=("Segoe UI", 10, "italic"), foreground="#374151", background="#f7f9fc", wraplength=420, justify=tk.RIGHT)
        self._msg_lbl.pack(side=tk.RIGHT)

    def update_stats(self, moves: int, incorrect_count: int):
        self._moves_var.set(f"Moves Used: {moves}")
        self._inc_var.set(f"Tiles Incorrect: {incorrect_count}")

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
