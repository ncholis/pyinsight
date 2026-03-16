"""Console rendering for trace trees."""

from __future__ import annotations

from pyinsight.events import TraceEvent


def render_tree(events: list[TraceEvent]) -> str:
    """Render the event list as a readable tree."""
    if not events:
        return ""

    by_parent: dict[str | None, list[TraceEvent]] = {}
    for event in events:
        by_parent.setdefault(event.parent_id, []).append(event)

    lines: list[str] = []
    roots = by_parent.get(None, [])
    for index, root in enumerate(roots):
        _render_event(lines, by_parent, root, prefix="", is_last=index == len(roots) - 1, is_root=True)
    return "\n".join(lines)


def _render_event(
    lines: list[str],
    by_parent: dict[str | None, list[TraceEvent]],
    event: TraceEvent,
    *,
    prefix: str,
    is_last: bool,
    is_root: bool,
) -> None:
    connector = "" if is_root else ("└── " if is_last else "├── ")
    suffix = " [SLOW]" if event.metadata.get("slow") else ""
    duration = f"{(event.duration_ms or 0.0):.2f}ms"
    status = " [ERROR]" if event.status == "error" else ""
    lines.append(f"{prefix}{connector}{event.name} {duration}{suffix}{status}")

    child_prefix = prefix + ("" if is_root else ("    " if is_last else "│   "))
    children = by_parent.get(event.event_id, [])
    for index, child in enumerate(children):
        _render_event(
            lines,
            by_parent,
            child,
            prefix=child_prefix,
            is_last=index == len(children) - 1,
            is_root=False,
        )
