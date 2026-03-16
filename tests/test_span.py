from __future__ import annotations

import json

from pyinsight import configure, span
from pyinsight.runtime import flush, reset_traces


def test_span_nesting_creates_tree(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    with span("root"):
        with span("child", phase="inner"):
            pass

    output = flush()
    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    events = payload["events"]
    assert [event["name"] for event in events] == ["root", "child"]
    assert events[1]["parent_id"] == events[0]["event_id"]
    assert events[1]["metadata"]["phase"] == "inner"
