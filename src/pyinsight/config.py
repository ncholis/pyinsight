"""Configuration primitives for pyinsight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Config:
    """Runtime output configuration."""

    enable_console: bool = True
    enable_json_export: bool = True
    output_dir: Path = Path("traces")
    overwrite_latest: bool = True
