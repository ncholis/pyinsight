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


def configure(
    *,
    enable_console: bool | None = None,
    enable_json_export: bool | None = None,
    output_dir: str | None = None,
    overwrite_latest: bool | None = None,
) -> Config:
    """Update the global configuration."""
    global _config
    if enable_console is not None:
        _config.enable_console = enable_console
    if enable_json_export is not None:
        _config.enable_json_export = enable_json_export
    if output_dir is not None:
        _config.output_dir = Path(output_dir)
    if overwrite_latest is not None:
        _config.overwrite_latest = overwrite_latest
    ensure_directory(_config.output_dir)
    return _config


def get_config() -> Config:
    """Return the current configuration."""
    return _config


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
            run_metadata={"event_count": len(events)},
        )

    _recorder.mark_flushed()
    return output_path


def _flush_at_exit() -> None:
    if _recorder.dirty and not _recorder.flushed:
        flush()


atexit.register(_flush_at_exit)
