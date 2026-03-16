"""Event recorder and context tracking."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from time import perf_counter_ns
from uuid import uuid4

from pyinsight.events import EventKind, EventStatus, TraceEvent
from pyinsight.utils import utc_now_iso


@dataclass(slots=True)
class ActiveEvent:
    """Context for an open event."""

    event: TraceEvent
    token: Token[str | None]


class TraceRecorder:
    """Collects trace events and preserves parent-child relationships."""

    def __init__(self) -> None:
        self._current_event_id: ContextVar[str | None] = ContextVar("pyinsight_current_event_id", default=None)
        self.reset()

    def reset(self) -> None:
        """Reset the recorder state for a fresh run."""
        self._events: list[TraceEvent] = []
        self._run_started_ns: int | None = None
        self._created_at: str = utc_now_iso()
        self._dirty = False
        self._flushed = False

    def start_event(self, *, name: str, kind: EventKind, metadata: dict[str, object] | None = None) -> ActiveEvent:
        """Open an event and make it the current parent for nested spans."""
        start_ns = perf_counter_ns()
        if self._run_started_ns is None:
            self._run_started_ns = start_ns
        parent_id = self._current_event_id.get()
        event = TraceEvent(
            event_id=uuid4().hex,
            parent_id=parent_id,
            name=name,
            kind=kind,
            start_ns=start_ns,
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        token = self._current_event_id.set(event.event_id)
        return ActiveEvent(event=event, token=token)

    def finish_event(
        self,
        active_event: ActiveEvent,
        *,
        status: EventStatus,
        metadata: dict[str, object] | None = None,
    ) -> TraceEvent:
        """Finalize an event and restore the parent context."""
        active_event.event.finish(end_ns=perf_counter_ns(), status=status, metadata=dict(metadata or {}))
        self._current_event_id.reset(active_event.token)
        self._dirty = True
        self._flushed = False
        return active_event.event

    def snapshot(self) -> list[TraceEvent]:
        """Return a shallow copy of the recorded events."""
        return list(self._events)

    def root_events(self) -> list[TraceEvent]:
        """Return top-level events in insertion order."""
        return [event for event in self._events if event.parent_id is None]

    def has_events(self) -> bool:
        """Return whether any events have been recorded."""
        return bool(self._events)

    def mark_flushed(self) -> None:
        """Mark the current event set as flushed."""
        self._flushed = True
        self._dirty = False

    @property
    def dirty(self) -> bool:
        """Whether there are unflushed events."""
        return self._dirty

    @property
    def flushed(self) -> bool:
        """Whether the latest state has already been flushed."""
        return self._flushed

    @property
    def created_at(self) -> str:
        """Run creation timestamp."""
        return self._created_at

    def total_duration_ms(self) -> float:
        """Return total duration across the run."""
        roots = self.root_events()
        if not roots:
            return 0.0
        total_ns = sum((event.end_ns or event.start_ns) - event.start_ns for event in roots)
        return round(total_ns / 1_000_000, 3)
