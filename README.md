# pyinsight

`pyinsight` is a lightweight runtime tracing toolkit for Python and AI workflows.

It exists to make function timing and nested execution flow visible without pulling in a large observability stack. The starter version focuses on a small API, clean console output, JSON trace export, and async-safe nesting.

## Why it exists

Tracing often starts with ad-hoc prints and timing blocks. That breaks down quickly once code becomes nested, asynchronous, or spread across a workflow. `pyinsight` provides:

- `trace` for sync and async function tracing
- `slow(threshold_ms)` for slow call detection
- `span(name, **metadata)` for manual nested blocks
- `configure(...)` for basic output control

## Installation

```bash
pip install -e .
```

For development tools:

```bash
pip install -e .[dev]
```

## Quickstart

```python
from pyinsight import configure, slow, span, trace

configure(enable_console=True, enable_json_export=True)

@trace
def fetch_users() -> list[str]:
    return ["alice", "bob"]

@slow(50)
def transform_users(users: list[str]) -> list[str]:
    with span("normalize_users", count=len(users)):
        return [user.upper() for user in users]

@trace
def main_pipeline() -> list[str]:
    users = fetch_users()
    return transform_users(users)

if __name__ == "__main__":
    main_pipeline()
```

Example console output:

```text
main_pipeline() 12.41ms
├── fetch_users() 1.14ms
└── transform_users() 10.98ms
    └── normalize_users 0.21ms
```

JSON traces are written to `traces/latest.json` by default.

## CLI usage

Run a Python file under tracing:

```bash
pyinsight run examples/basic_demo.py
```

Read and summarize a trace file:

```bash
pyinsight report traces/latest.json
```

## Examples

Runnable examples are available in `examples/basic_demo.py`, `examples/nested_demo.py`, and `examples/async_demo.py`.

## Development setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Testing

```bash
pytest
```

## Project layout

```text
src/pyinsight/   library code
tests/           pytest suite
examples/        runnable demos
traces/          exported trace files
```

## Roadmap

- richer metadata formatting
- optional OpenTelemetry exporter
- filtering and sampling
- plugin hooks for AI provider integrations

## License

MIT
