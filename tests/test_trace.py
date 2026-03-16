from __future__ import annotations

import json

import pytest

from pyinsight import configure, trace
from pyinsight.runtime import flush, reset_traces


def test_trace_records_nested_sync_calls(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    @trace
    def child() -> str:
        return "ok"

    @trace
    def parent() -> str:
        return child()

    assert parent() == "ok"
    output = flush()

    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    events = payload["events"]
    assert len(events) == 2
    assert events[0]["name"] == "parent()"
    assert events[1]["parent_id"] == events[0]["event_id"]


def test_trace_records_error_metadata_for_sync_functions(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    @trace
    def explode() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        explode()

    output = flush()
    assert output is not None

    payload = json.loads(output.read_text(encoding="utf-8"))
    event = payload["events"][0]
    assert event["status"] == "error"
    assert event["metadata"]["exception_type"] == "ValueError"
    assert event["metadata"]["exception_message"] == "boom"
