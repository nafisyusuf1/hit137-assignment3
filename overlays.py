import cv2
import numpy as np
from abc import ABC, abstractmethod


class Overlay(ABC):
    """Abstract base class for visual overlays (Encapsulation, Inheritance, Polymorphism)."""
    def __init__(self, color: tuple, thickness: int = 2):
        self._color = color
        self._thickness = thickness

    @property
    def color(self) -> tuple:
        return self._color

    @abstractmethod
    def draw(self, image: np.ndarray, grid_size: int, **kwargs) -> np.ndarray:
        pass

    @staticmethod
    def get_tile_bounds(image: np.ndarray, grid_size: int, row: int, col: int) -> tuple:
        h, w = image.shape[:2]
        th, tw = h // grid_size, w // grid_size
        x1, y1 = col * tw, row * th
        return x1, y1, x1 + tw, y1 + th


class GridOverlay(Overlay):
    """Draws a subtle grid and stronger tile separators over the transformed image."""
    def __init__(self, color: tuple = (220, 220, 220), thickness: int = 1, alpha: float = 0.55):
        super().__init__(color, thickness)
        self._alpha = alpha

    def draw(self, image: np.ndarray, grid_size: int, **kwargs) -> np.ndarray:
        out = image.copy()
        layer = image.copy()
        h, w = out.shape[:2]
        th, tw = h // grid_size, w // grid_size
        for i in range(1, grid_size):
            cv2.line(layer, (i * tw, 0), (i * tw, h), self._color, self._thickness + 1, cv2.LINE_AA)
            cv2.line(layer, (0, i * th), (w, i * th), self._color, self._thickness + 1, cv2.LINE_AA)
        cv2.addWeighted(layer, self._alpha, out, 1 - self._alpha, 0, out)
        return out


class SelectionOverlay(Overlay):
    """Highlights the selected tile with a stronger outline and glow."""
    def __init__(self, color: tuple = (0, 200, 255), thickness: int = 4):
        super().__init__(color, thickness)

    def draw(self, image: np.ndarray, grid_size: int, **kwargs) -> np.ndarray:
        pos = kwargs.get("selected_pos")
        if pos is None:
            return image
        out = image.copy()
        x1, y1, x2, y2 = self.get_tile_bounds(out, grid_size, pos[0], pos[1])
        pad = max(3, self._thickness)
        cv2.rectangle(out, (x1 + pad, y1 + pad), (x2 - pad, y2 - pad), self._color, self._thickness + 1, cv2.LINE_AA)
        cv2.rectangle(out, (x1 + 2, y1 + 2), (x2 - 2, y2 - 2), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.line(out, (x1 + pad, y1 + pad), (x2 - pad, y1 + pad), (255, 255, 255), 1, cv2.LINE_AA)
        return out


class TickOverlay(Overlay):
    """Draws a green check mark on correctly placed tiles."""
    def __init__(self, color: tuple = (24, 180, 24), thickness: int = 2):
        super().__init__(color, thickness)

    def draw(self, image: np.ndarray, grid_size: int, **kwargs) -> np.ndarray:
        correct = kwargs.get("correct_positions", [])
        if not correct:
            return image
        out = image.copy()
        for r, c in correct:
            x1, y1, x2, y2 = self.get_tile_bounds(out, grid_size, r, c)
            radius = max(10, min(x2 - x1, y2 - y1) // 7)
            cx, cy = x2 - radius - 8, y1 + radius + 8
            cv2.circle(out, (cx, cy), radius + 2, (20, 120, 20), -1, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), radius, self._color, -1, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), radius, (255, 255, 255), 1, cv2.LINE_AA)
            p1 = (int(cx - radius * 0.45), int(cy))
            p2 = (int(cx - radius * 0.1), int(cy + radius * 0.38))
            p3 = (int(cx + radius * 0.5), int(cy - radius * 0.35))
            cv2.line(out, p1, p2, (255, 255, 255), self._thickness + 1, cv2.LINE_AA)
            cv2.line(out, p2, p3, (255, 255, 255), self._thickness + 1, cv2.LINE_AA)
        return out


class HintOverlay(Overlay):
    """Draws a highlighted ring on the hinted tile and home position."""
    def __init__(self, color: tuple = (255, 120, 30), thickness: int = 3):
        super().__init__(color, thickness)

    def draw(self, image: np.ndarray, grid_size: int, **kwargs) -> np.ndarray:
        pos = kwargs.get("hint_pos")
        if pos is None:
            return image
        out = image.copy()
        x1, y1, x2, y2 = self.get_tile_bounds(out, grid_size, pos[0], pos[1])
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        rad = int(min(x2 - x1, y2 - y1) * 0.35)
        cv2.circle(out, (cx, cy), rad + 4, (255, 255, 255), self._thickness + 2, cv2.LINE_AA)
        cv2.circle(out, (cx, cy), rad, self._color, self._thickness, cv2.LINE_AA)
        cv2.circle(out, (cx, cy), max(10, rad // 4), (255, 255, 255), -1, cv2.LINE_AA)
        return out


class OverlayRenderer:
    """Applies all overlays polymorphically onto the original and transformed images."""
    def __init__(self):
        self._grid = GridOverlay()
        self._sel = SelectionOverlay()
        self._tick = TickOverlay()
        self._hint = HintOverlay()

    def render_original(self, image: np.ndarray, grid_size: int, hint_home_pos: tuple = None) -> np.ndarray:
        if image is None:
            return None
        return self._hint.draw(image, grid_size, hint_pos=hint_home_pos)

    def render_transformed(self, image: np.ndarray, grid_size: int, selected_pos=None, correct_positions=None, hint_curr_pos=None) -> np.ndarray:
        if image is None:
            return None
        pipeline = [
            (self._grid, {}),
            (self._tick, {"correct_positions": correct_positions or []}),
            (self._sel, {"selected_pos": selected_pos}),
            (self._hint, {"hint_pos": hint_curr_pos}),
        ]
        res = image.copy()
        for ov, params in pipeline:
            res = ov.draw(res, grid_size, **params)
        return res
