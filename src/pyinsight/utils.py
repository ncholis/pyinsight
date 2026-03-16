"""Internal helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def default_callable_name(func: Any) -> str:
    """Build a readable display name for a callable."""
    return f"{getattr(func, '__name__', func.__class__.__name__)}()"


def ensure_directory(path: Path) -> None:
    """Create a directory when it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def exception_metadata(exc_type: type[BaseException] | None, exc: BaseException | None) -> dict[str, str]:
    """Serialize exception details for event metadata."""
    if exc_type is None or exc is None:
        return {}
    return {"error_type": exc_type.__name__, "error_message": str(exc)}


def status_from_exception(exc_type: type[BaseException] | None) -> str:
    """Map exception presence to event status."""
    return "error" if exc_type is not None else "ok"


ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]
