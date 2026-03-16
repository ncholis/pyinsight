from __future__ import annotations

from pyinsight.console import render_tree
from pyinsight.events import TraceEvent


def test_render_tree_handles_deep_nesting_and_markers() -> None:
    events = [
        TraceEvent(
            event_id="1",
            parent_id=None,
            name="pipeline",
            kind="trace",
            start_ns=0,
            end_ns=100,
            duration_ms=100.0,
        ),
        TraceEvent(
            event_id="2",
            parent_id="1",
            name="fetch_users()",
            kind="trace",
            start_ns=0,
            end_ns=20,
            duration_ms=20.0,
        ),
        TraceEvent(
            event_id="3",
            parent_id="1",
            name="transform_users()",
            kind="trace",
            start_ns=20,
            end_ns=80,
            duration_ms=60.0,
        ),
        TraceEvent(
            event_id="4",
            parent_id="3",
            name="normalize_user()",
            kind="span",
            start_ns=30,
            end_ns=40,
            duration_ms=10.0,
        ),
        TraceEvent(
            event_id="5",
            parent_id="1",
            name="save_users()",
            kind="trace",
            start_ns=80,
            end_ns=100,
            duration_ms=20.0,
            status="error",
            metadata={"slow": True},
        ),
    ]

    rendered = render_tree(events)

    assert rendered == "\n".join(
        [
            "pipeline 100.00ms",
            "├── fetch_users() 20.00ms",
            "├── transform_users() 60.00ms",
            "│   └── normalize_user() 10.00ms",
            "└── save_users() 20.00ms [SLOW] [ERROR]",
        ]
    )
