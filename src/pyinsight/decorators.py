"""Tracing decorators."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

from pyinsight.spans import create_span
from pyinsight.utils import default_callable_name

P = ParamSpec("P")
R = TypeVar("R")


@overload
def trace(func: Callable[P, R]) -> Callable[P, R]:
    ...


@overload
def trace(*, name: str | None = None, **metadata: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    ...


def trace(
    func: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    **metadata: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    """Trace sync or async callables."""

    def decorator(target: Callable[P, R]) -> Callable[P, R]:
        span_name = name or default_callable_name(target)

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                async with create_span(span_name, kind="trace", metadata=metadata):
                    return await target(*args, **kwargs)  # type: ignore[misc]

            return async_wrapper  # type: ignore[return-value]

        @wraps(target)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with create_span(span_name, kind="trace", metadata=metadata):
                return target(*args, **kwargs)

        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


def slow(threshold_ms: float) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Mark a traced call as slow when it exceeds the threshold."""

    def decorator(target: Callable[P, R]) -> Callable[P, R]:
        span_name = default_callable_name(target)
        metadata = {"slow_threshold_ms": threshold_ms}

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                async with create_span(
                    span_name,
                    kind="trace",
                    slow_threshold_ms=threshold_ms,
                    metadata=metadata,
                ):
                    return await target(*args, **kwargs)  # type: ignore[misc]

            return async_wrapper  # type: ignore[return-value]

        @wraps(target)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with create_span(
                span_name,
                kind="trace",
                slow_threshold_ms=threshold_ms,
                metadata=metadata,
            ):
                return target(*args, **kwargs)

        return sync_wrapper

    return decorator
