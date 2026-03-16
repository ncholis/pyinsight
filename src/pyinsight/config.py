"""Configuration primitives for pyinsight."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True)
class Config:
    """Runtime output configuration.

    The config is treated as immutable so runtime updates remain explicit.
    `configure(...)` replaces the active config with an updated copy.
    """

    enable_console: bool = True
    enable_json_export: bool = True
    output_dir: Path = field(default_factory=lambda: Path("traces"))
    overwrite_latest: bool = True
    quiet: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", Path(self.output_dir))

    def updated(
        self,
        *,
        enable_console: bool | None = None,
        enable_json_export: bool | None = None,
        output_dir: str | Path | None = None,
        overwrite_latest: bool | None = None,
        quiet: bool | None = None,
    ) -> Self:
        """Return a copy with only the provided fields changed."""
        return replace(
            self,
            enable_console=self.enable_console if enable_console is None else enable_console,
            enable_json_export=self.enable_json_export if enable_json_export is None else enable_json_export,
            output_dir=self.output_dir if output_dir is None else Path(output_dir),
            overwrite_latest=self.overwrite_latest if overwrite_latest is None else overwrite_latest,
            quiet=self.quiet if quiet is None else quiet,
        )
