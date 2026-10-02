"""Persistent best completion times for each supported puzzle size."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Optional


class BestTimes:
    """Read and update the local best time for each puzzle grid size."""

    GRID_SIZES = (3, 4, 5)

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path if path is not None else self._default_path()

    @staticmethod
    def _default_path() -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        return base / "puzzle-studio" / "best_times.json"

    def best_for(self, grid_size: int) -> Optional[float]:
        self._validate_grid_size(grid_size)
        return self._read().get(str(grid_size))

    def record(self, grid_size: int, elapsed_seconds: float) -> tuple[bool, float]:
        """Save a new personal best and return (is_new_best, best_time)."""
        self._validate_grid_size(grid_size)
        if (
            isinstance(elapsed_seconds, bool)
            or not isinstance(elapsed_seconds, (int, float))
            or not math.isfinite(elapsed_seconds)
            or elapsed_seconds < 0
        ):
            raise ValueError("Elapsed time must be a finite non-negative number.")

        records = self._read()
        key = str(grid_size)
        current = records.get(key)
        if current is not None and elapsed_seconds >= current:
            return False, current

        best = float(elapsed_seconds)
        records[key] = best
        self._write(records)
        return True, best

    def _read(self) -> dict[str, float]:
        try:
            content = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        try:
            records = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"Best-time file contains invalid JSON: {self._path}") from error
        if not isinstance(records, dict):
            raise ValueError(f"Best-time file must contain a JSON object: {self._path}")

        validated: dict[str, float] = {}
        for key, value in records.items():
            if key not in {str(size) for size in self.GRID_SIZES}:
                raise ValueError(f"Unsupported puzzle size in best-time file: {key}")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"Invalid best time for {key}x{key} puzzle.")
            validated[key] = float(value)
        return validated

    def _write(self, records: dict[str, float]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f"{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(records, temporary_file, indent=2, sort_keys=True)
                temporary_file.write("\n")
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path is not None and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    @classmethod
    def _validate_grid_size(cls, grid_size: int) -> None:
        if (
            isinstance(grid_size, bool)
            or not isinstance(grid_size, int)
            or grid_size not in cls.GRID_SIZES
        ):
            raise ValueError("Grid size must be 3, 4, or 5.")
