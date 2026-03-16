from __future__ import annotations

import asyncio
import json

from pyinsight import configure, slow, span, trace
from pyinsight.runtime import flush, reset_traces


def test_trace_supports_async_nesting(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    @trace
    async def child() -> str:
        await asyncio.sleep(0)
        return "child"

    @slow(0)
    async def parent() -> str:
        async with span("manual"):
            return await child()

    result = asyncio.run(parent())
    output = flush()

    assert result == "child"
    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    events = payload["events"]
    assert [event["name"] for event in events] == ["parent()", "manual", "child()"]
    assert events[1]["parent_id"] == events[0]["event_id"]
    assert events[2]["parent_id"] == events[1]["event_id"]
    assert events[0]["metadata"]["slow"] is True
