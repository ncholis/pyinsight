from __future__ import annotations

import json

import pytest

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


def test_span_records_error_metadata(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    with pytest.raises(KeyError, match="missing"):
        with span("root_span"):
            raise KeyError("missing")

    output = flush()
    assert output is not None

    payload = json.loads(output.read_text(encoding="utf-8"))
    event = payload["events"][0]
    assert event["status"] == "error"
    assert event["metadata"]["exception_type"] == "KeyError"
    assert "missing" in event["metadata"]["exception_message"]
