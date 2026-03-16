from __future__ import annotations

import asyncio

from pyinsight import configure, slow, span, trace

configure(enable_console=True, enable_json_export=True)


@trace
async def fetch_remote() -> str:
    await asyncio.sleep(0.01)
    return "payload"


@slow(5)
async def async_pipeline() -> str:
    async with span("prepare_request", component="demo"):
        await asyncio.sleep(0)
    return await fetch_remote()


if __name__ == "__main__":
    asyncio.run(async_pipeline())
