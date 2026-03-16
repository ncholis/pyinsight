from __future__ import annotations

import time

from pyinsight import configure, slow, span, trace

configure(enable_console=True, enable_json_export=True)


@trace
def fetch_users() -> list[str]:
    time.sleep(0.02)
    return ["alice", "bob", "carol"]


@slow(10)
def transform_users(users: list[str]) -> list[str]:
    with span("normalize_users", count=len(users)):
        time.sleep(0.015)
        return [user.upper() for user in users]


@trace
def main_pipeline() -> list[str]:
    users = fetch_users()
    return transform_users(users)


if __name__ == "__main__":
    main_pipeline()
