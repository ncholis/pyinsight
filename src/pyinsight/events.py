"""Trace event data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

EventKind = Literal["trace", "span"]
EventStatus = Literal["ok", "error"]


@dataclass(slots=True)
class TraceEvent:
    """A single timed execution event."""

    event_id: str
    parent_id: str | None
    name: str
    kind: EventKind
    start_ns: int
    end_ns: int | None = None
    duration_ms: float | None = None
    status: EventStatus = "ok"
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self, *, end_ns: int, status: EventStatus, metadata: dict[str, Any] | None = None) -> None:
        """Finalize the event timing and metadata."""
        self.end_ns = end_ns
        self.duration_ms = round((end_ns - self.start_ns) / 1_000_000, 3)
        self.status = status
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event for JSON export."""
        return {
            "event_id": self.event_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "start_ns": self.start_ns,
            "end_ns": self.end_ns,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "metadata": self.metadata,
        }
