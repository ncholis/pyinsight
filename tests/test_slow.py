from __future__ import annotations

import json
import time

from pyinsight import configure, slow
from pyinsight.runtime import flush, reset_traces


def test_slow_marks_event_metadata(tmp_path) -> None:
    reset_traces()
    configure(enable_console=False, enable_json_export=True, output_dir=str(tmp_path))

    @slow(5)
    def sleepy() -> None:
        time.sleep(0.01)

    sleepy()
    output = flush()

    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    event = payload["events"][0]
    assert event["metadata"]["slow"] is True
    assert event["metadata"]["slow_threshold_ms"] == 5
