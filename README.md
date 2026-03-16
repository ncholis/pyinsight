# pyinsight

`pyinsight` is a lightweight runtime tracing toolkit for Python and AI workflows.

It exists to make function timing and nested execution flow visible without pulling in a large observability stack. The current version focuses on a small API, clean console output, JSON trace export, async-safe nesting, and practical trace reporting.

## Why it exists

Tracing often starts with ad-hoc prints and timing blocks. That breaks down quickly once code becomes nested, asynchronous, or spread across a workflow. `pyinsight` provides:

- `trace` for sync and async function tracing
- `slow(threshold_ms)` for slow call detection
- `span(name, **metadata)` for manual nested blocks
- `configure(...)` for basic output control
- `pyinsight run` and `pyinsight report` for quick inspection from the CLI

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

Markers:

- `[SLOW]` means the event crossed a configured slow threshold
- `[ERROR]` means the traced function or span raised an exception

JSON traces are written to `traces/latest.json` by default unless configured otherwise.

## Configuration

Use `configure(...)` to control runtime output behavior:

```python
from pyinsight import configure

configure(
    enable_console=True,
    enable_json_export=True,
    output_dir="traces",
    overwrite_latest=True,
    quiet=False,
)
```

Notes:

- omitted config values keep the current setting
- `output_dir` controls where JSON traces are written
- `overwrite_latest=False` keeps history by writing timestamped trace files
- `quiet=True` suppresses non-essential CLI messages

## CLI usage

Run a Python file under tracing:

```bash
pyinsight run examples/basic_demo.py
```

Common run flags:

```bash
pyinsight run examples/basic_demo.py --no-console
pyinsight run examples/basic_demo.py --output-dir custom_traces
pyinsight run examples/basic_demo.py --keep-history
pyinsight run examples/basic_demo.py --no-json --quiet
```

Read and summarize a trace file:

```bash
pyinsight report traces/latest.json
```

Common report flags:

```bash
pyinsight report traces/latest.json --top 3
pyinsight report traces/latest.json --kind trace
pyinsight report traces/latest.json --status error
pyinsight report traces/latest.json --json
```

Example report output:

```text
Trace file: C:\path\to\traces\latest.json
Created at: 2026-03-17T00:00:00+00:00
Total events: 4
Total duration: 110.00ms
Average duration: 47.50ms
Max duration: 100.00ms
Slow events: 1 (25.00%)
Error events: 1
Root events: 2
Deepest nesting depth: 2
Events with metadata: 2
Event counts by kind:
- span: 1
- trace: 3
Top slowest events:
- pipeline 100.00ms
- normalize 50.00ms [SLOW]
- save 30.00ms [ERROR]
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
python -m pytest
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
- filtering and sampling

## License

MIT
