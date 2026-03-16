"""Command-line interface for pyinsight."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from pyinsight.exporters import load_trace
from pyinsight.runtime import configure, flush, reset_traces


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="pyinsight", description="Runtime tracing for Python workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a Python file with tracing enabled.")
    run_parser.add_argument("python_file", help="Path to the target Python script.")

    report_parser = subparsers.add_parser("report", help="Print a summary from a JSON trace file.")
    report_parser.add_argument("json_trace_file", help="Path to a JSON trace file.")
    return parser


def run_file(python_file: str) -> int:
    """Execute a script and emit traces."""
    script_path = Path(python_file).resolve()
    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        return 1

    reset_traces()
    configure(enable_console=True, enable_json_export=True, output_dir="traces", overwrite_latest=True)

    original_argv = sys.argv[:]
    original_path = list(sys.path)
    sys.argv = [str(script_path)]
    sys.path.insert(0, str(script_path.parent))
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        flush()
        sys.argv = original_argv
        sys.path[:] = original_path
    return 0


def report_trace(json_trace_file: str) -> int:
    """Read a trace file and print a summary report."""
    trace_path = Path(json_trace_file).resolve()
    if not trace_path.exists():
        print(f"Trace file not found: {trace_path}", file=sys.stderr)
        return 1

    payload = load_trace(trace_path)
    events = payload.get("events", [])
    total_duration = payload.get("total_duration_ms", 0.0)
    slow_events = [event for event in events if event.get("metadata", {}).get("slow")]
    top_slowest = sorted(events, key=lambda item: item.get("duration_ms") or 0.0, reverse=True)[:5]

    print(f"Trace file: {trace_path}")
    print(f"Total events: {len(events)}")
    print(f"Total duration: {float(total_duration):.2f}ms")
    print(f"Slow events: {len(slow_events)}")
    print("Top slowest events:")
    for event in top_slowest:
        print(f"- {event.get('name')} {float(event.get('duration_ms') or 0.0):.2f}ms")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_file(args.python_file)
    if args.command == "report":
        return report_trace(args.json_trace_file)
    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
