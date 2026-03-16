"""Global runtime state for pyinsight."""

from __future__ import annotations

import atexit
from pathlib import Path

from pyinsight.config import Config
from pyinsight.console import render_tree
from pyinsight.exporters import export_json
from pyinsight.recorder import TraceRecorder
from pyinsight.utils import ensure_directory

_config = Config()
_recorder = TraceRecorder()
_config_overrides: dict[str, object] = {}


def _apply_config_overrides(config: Config) -> Config:
    """Apply any active internal config overrides."""
    if not _config_overrides:
        return config
    return config.updated(
        enable_console=_config_overrides.get("enable_console"),  # type: ignore[arg-type]
        enable_json_export=_config_overrides.get("enable_json_export"),  # type: ignore[arg-type]
        output_dir=_config_overrides.get("output_dir"),  # type: ignore[arg-type]
        overwrite_latest=_config_overrides.get("overwrite_latest"),  # type: ignore[arg-type]
        quiet=_config_overrides.get("quiet"),  # type: ignore[arg-type]
    )


def configure(
    *,
    enable_console: bool | None = None,
    enable_json_export: bool | None = None,
    output_dir: str | None = None,
    overwrite_latest: bool | None = None,
    quiet: bool | None = None,
) -> Config:
    """Update the global runtime configuration.

    Only provided values are changed; omitted values keep the current setting.
    """
    global _config
    _config = _apply_config_overrides(
        _config.updated(
        enable_console=enable_console,
        enable_json_export=enable_json_export,
        output_dir=output_dir,
        overwrite_latest=overwrite_latest,
        quiet=quiet,
        )
    )
    ensure_directory(_config.output_dir)
    return _config


def get_config() -> Config:
    """Return the current configuration."""
    return _config


def set_config(config: Config) -> Config:
    """Replace the active configuration with a provided config object."""
    global _config
    _config = _apply_config_overrides(config)
    ensure_directory(_config.output_dir)
    return _config


def set_config_overrides(
    *,
    enable_console: bool | None = None,
    enable_json_export: bool | None = None,
    output_dir: str | None = None,
    overwrite_latest: bool | None = None,
    quiet: bool | None = None,
) -> None:
    """Set internal overrides that take precedence over subsequent configure calls."""
    global _config_overrides
    overrides: dict[str, object] = {}
    if enable_console is not None:
        overrides["enable_console"] = enable_console
    if enable_json_export is not None:
        overrides["enable_json_export"] = enable_json_export
    if output_dir is not None:
        overrides["output_dir"] = output_dir
    if overwrite_latest is not None:
        overrides["overwrite_latest"] = overwrite_latest
    if quiet is not None:
        overrides["quiet"] = quiet
    _config_overrides = overrides
    set_config(_config)


def clear_config_overrides() -> None:
    """Clear any active internal config overrides."""
    global _config_overrides
    _config_overrides = {}


def get_recorder() -> TraceRecorder:
    """Return the global recorder."""
    return _recorder


def reset_traces() -> None:
    """Reset trace state for a new run."""
    _recorder.reset()


def flush() -> Path | None:
    """Emit console output and write JSON exports for the current trace run."""
    if not _recorder.has_events() or _recorder.flushed:
        return None

    events = _recorder.snapshot()
    total_duration_ms = _recorder.total_duration_ms()
    if _config.enable_console:
        tree = render_tree(events)
        if tree:
            print(tree)

    output_path: Path | None = None
    if _config.enable_json_export:
        ensure_directory(_config.output_dir)
        if _config.overwrite_latest:
            output_path = _config.output_dir / "latest.json"
        else:
            timestamp = _recorder.created_at.replace(":", "-")
            output_path = _config.output_dir / f"trace-{timestamp}.json"
        output_path = export_json(
            output_path=output_path,
            events=events,
            created_at=_recorder.created_at,
            total_duration_ms=total_duration_ms,
            run_metadata={
                "event_count": len(events),
                "root_event_count": len(_recorder.root_events()),
            },
        )

    _recorder.mark_flushed()
    return output_path


def _flush_at_exit() -> None:
    if _recorder.dirty and not _recorder.flushed:
        flush()


atexit.register(_flush_at_exit)
