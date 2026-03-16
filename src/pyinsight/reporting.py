"""Helpers for trace file analysis and report generation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pyinsight.exporters import load_trace

TracePayload = dict[str, Any]
TraceEventRecord = dict[str, Any]


def load_trace_file(path: str | Path) -> TracePayload:
    """Load and normalize a trace JSON file."""
    return load_trace(Path(path))


def filter_events(
    events: list[TraceEventRecord],
    *,
    kind: str | None = None,
    status: str | None = None,
) -> list[TraceEventRecord]:
    """Filter events by kind and status."""
    filtered: list[TraceEventRecord] = []
    for event in events:
        if kind is not None and event.get("kind") != kind:
            continue
        if status is not None and event.get("status") != status:
            continue
        filtered.append(event)
    return filtered


def top_slowest_events(events: list[TraceEventRecord], n: int = 5) -> list[TraceEventRecord]:
    """Return the top slowest events in descending order."""
    if n <= 0:
        return []
    ordered = sorted(events, key=lambda event: float(event.get("duration_ms") or 0.0), reverse=True)
    return [
        {
            "name": event.get("name"),
            "kind": event.get("kind"),
            "status": event.get("status"),
            "duration_ms": round(float(event.get("duration_ms") or 0.0), 3),
            "metadata": event.get("metadata", {}),
        }
        for event in ordered[:n]
    ]


def compute_tree_depth(events: list[TraceEventRecord]) -> int:
    """Compute the deepest nesting depth within the provided events."""
    if not events:
        return 0

    event_ids = {str(event.get("event_id")) for event in events}
    children_by_parent: dict[str | None, list[TraceEventRecord]] = {}
    for event in events:
        parent_id = event.get("parent_id")
        normalized_parent = str(parent_id) if parent_id in event_ids else None
        children_by_parent.setdefault(normalized_parent, []).append(event)

    def walk(event: TraceEventRecord, depth: int) -> int:
        children = children_by_parent.get(str(event.get("event_id")), [])
        if not children:
            return depth
        return max(walk(child, depth + 1) for child in children)

    roots = children_by_parent.get(None, [])
    return max(walk(root, 1) for root in roots) if roots else 0


def summarize_events(events: list[TraceEventRecord]) -> dict[str, Any]:
    """Compute aggregate statistics for a list of trace events."""
    total_events = len(events)
    event_ids = {str(event.get("event_id")) for event in events}
    root_events = [event for event in events if event.get("parent_id") not in event_ids]
    durations = [float(event.get("duration_ms") or 0.0) for event in events]
    total_duration = round(sum(float(event.get("duration_ms") or 0.0) for event in root_events), 3)
    slow_count = sum(1 for event in events if event.get("metadata", {}).get("slow"))
    error_count = sum(1 for event in events if event.get("status") == "error")
    metadata_count = sum(1 for event in events if event.get("metadata"))
    kind_counts = dict(sorted(Counter(str(event.get("kind", "unknown")) for event in events).items()))

    return {
        "total_events": total_events,
        "total_duration_ms": total_duration,
        "average_duration_ms": round(sum(durations) / total_events, 3) if total_events else 0.0,
        "max_duration_ms": round(max(durations), 3) if durations else 0.0,
        "slow_events": slow_count,
        "error_events": error_count,
        "root_events": len(root_events),
        "deepest_nesting_depth": compute_tree_depth(events),
        "events_with_metadata": metadata_count,
        "slow_percentage": round((slow_count / total_events) * 100, 2) if total_events else 0.0,
        "event_counts_by_kind": kind_counts,
    }


def build_report_summary(
    trace_path: str | Path,
    *,
    kind: str | None = None,
    status: str | None = None,
    top: int = 5,
) -> dict[str, Any]:
    """Build a report summary from a trace file."""
    resolved_path = Path(trace_path).resolve()
    payload = load_trace_file(resolved_path)
    events = filter_events(payload.get("events", []), kind=kind, status=status)
    summary = summarize_events(events)
    summary.update(
        {
            "trace_file": str(resolved_path),
            "created_at": payload.get("created_at"),
            "filters": {"kind": kind, "status": status},
            "top_slowest_events": top_slowest_events(events, n=top),
        }
    )
    return summary


def render_summary(summary: dict[str, Any]) -> str:
    """Render a human-readable report summary."""
    lines = [f"Trace file: {summary['trace_file']}"]
    created_at = summary.get("created_at")
    if created_at:
        lines.append(f"Created at: {created_at}")

    filters = summary.get("filters", {})
    active_filters = [f"{name}={value}" for name, value in filters.items() if value is not None]
    if active_filters:
        lines.append(f"Filters: {', '.join(active_filters)}")

    lines.extend(
        [
            f"Total events: {summary['total_events']}",
            f"Total duration: {float(summary['total_duration_ms']):.2f}ms",
            f"Average duration: {float(summary['average_duration_ms']):.2f}ms",
            f"Max duration: {float(summary['max_duration_ms']):.2f}ms",
            f"Slow events: {summary['slow_events']} ({float(summary['slow_percentage']):.2f}%)",
            f"Error events: {summary['error_events']}",
            f"Root events: {summary['root_events']}",
            f"Deepest nesting depth: {summary['deepest_nesting_depth']}",
            f"Events with metadata: {summary['events_with_metadata']}",
            "Event counts by kind:",
        ]
    )

    kind_counts = summary.get("event_counts_by_kind", {})
    if kind_counts:
        for kind, count in kind_counts.items():
            lines.append(f"- {kind}: {count}")
    else:
        lines.append("- none")

    lines.append("Top slowest events:")
    top_events = summary.get("top_slowest_events", [])
    if top_events:
        for event in top_events:
            markers: list[str] = []
            metadata = event.get("metadata", {})
            if metadata.get("slow"):
                markers.append("SLOW")
            if event.get("status") == "error":
                markers.append("ERROR")
            marker_suffix = "".join(f" [{marker}]" for marker in markers)
            lines.append(f"- {event.get('name')} {float(event.get('duration_ms') or 0.0):.2f}ms{marker_suffix}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def render_summary_json(summary: dict[str, Any]) -> str:
    """Render a summary as formatted JSON."""
    return json.dumps(summary, indent=2)
