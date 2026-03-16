from __future__ import annotations

import time

from pyinsight import configure, trace

configure(enable_console=True, enable_json_export=True)


@trace
def fetch_users() -> list[str]:
    time.sleep(0.01)
    return ["alice", "bob"]


if __name__ == "__main__":
    fetch_users()
