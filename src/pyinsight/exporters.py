"""Export utilities for persisted traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyinsight.events import TraceEvent
from pyinsight.utils import ensure_directory


def export_json(
    *,
    output_path: Path,
    events: list[TraceEvent],
    created_at: str,
    total_duration_ms: float,
    run_metadata: dict[str, object],
) -> Path:
    """Write the trace payload to a JSON file."""
    ensure_directory(output_path.parent)
    payload = {
        "created_at": created_at,
        "run": run_metadata,
        "total_duration_ms": total_duration_ms,
        "events": [event.to_dict() for event in events],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def load_trace(path: Path) -> dict[str, Any]:
    """Load a previously exported JSON trace."""
    return json.loads(path.read_text(encoding="utf-8"))
