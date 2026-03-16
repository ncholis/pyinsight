"""Manual tracing span context managers."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any

from pyinsight.recorder import ActiveEvent
from pyinsight.runtime import get_recorder
from pyinsight.utils import ExcInfo, exception_metadata, status_from_exception


class SpanContext(AbstractContextManager["SpanContext"], AbstractAsyncContextManager["SpanContext"]):
    """A manual tracing span."""

    def __init__(
        self,
        name: str,
        *,
        kind: str = "span",
        metadata: dict[str, Any] | None = None,
        slow_threshold_ms: float | None = None,
    ) -> None:
        self._name = name
        self._kind = kind
        self._metadata = dict(metadata or {})
        self._slow_threshold_ms = slow_threshold_ms
        self._active_event: ActiveEvent | None = None

    def __enter__(self) -> "SpanContext":
        recorder = get_recorder()
        metadata = dict(self._metadata)
        if self._slow_threshold_ms is not None:
            metadata["slow_threshold_ms"] = self._slow_threshold_ms
        self._active_event = recorder.start_event(name=self._name, kind=self._kind, metadata=metadata)
        return self

    def __exit__(self, exc_type: ExcInfo[0], exc: ExcInfo[1], _: ExcInfo[2]) -> bool:
        if self._active_event is None:
            return False
        recorder = get_recorder()
        final_metadata = exception_metadata(exc_type, exc)
        event = recorder.finish_event(
            self._active_event,
            status=status_from_exception(exc_type),  # type: ignore[arg-type]
            metadata=final_metadata,
        )
        if self._slow_threshold_ms is not None and event.duration_ms is not None:
            event.metadata["slow"] = event.duration_ms >= self._slow_threshold_ms
        return False

    async def __aenter__(self) -> "SpanContext":
        return self.__enter__()

    async def __aexit__(self, exc_type: ExcInfo[0], exc: ExcInfo[1], tb: ExcInfo[2]) -> bool:
        return self.__exit__(exc_type, exc, tb)


def create_span(
    name: str,
    *,
    kind: str = "span",
    slow_threshold_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> SpanContext:
    """Internal factory for span contexts."""
    return SpanContext(name=name, kind=kind, slow_threshold_ms=slow_threshold_ms, metadata=metadata)


def span(name: str, **metadata: Any) -> SpanContext:
    """Create a manual tracing span."""
    return create_span(name=name, kind="span", metadata=metadata)
