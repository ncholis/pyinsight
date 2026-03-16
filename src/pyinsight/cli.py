"""Command-line interface for pyinsight."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from pyinsight.reporting import build_report_summary, render_summary, render_summary_json
from pyinsight.runtime import (
    clear_config_overrides,
    configure,
    flush,
    get_config,
    reset_traces,
    set_config,
    set_config_overrides,
)


def non_negative_int(value: str) -> int:
    """Argparse validator for non-negative integers."""
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="pyinsight", description="Runtime tracing for Python workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a Python file with tracing enabled.")
    run_parser.add_argument("python_file", help="Path to the target Python script.")
    run_parser.add_argument("--no-console", action="store_true", help="Disable console tree output.")
    run_parser.add_argument("--no-json", action="store_true", help="Disable JSON trace export.")
    run_parser.add_argument("--output-dir", help="Write trace files to a custom directory.")
    run_parser.add_argument("--keep-history", action="store_true", help="Write timestamped trace files.")
    run_parser.add_argument("--quiet", action="store_true", help="Suppress non-essential CLI messages.")

    report_parser = subparsers.add_parser("report", help="Print a summary from a JSON trace file.")
    report_parser.add_argument("json_trace_file", help="Path to a JSON trace file.")
    report_parser.add_argument("--top", type=non_negative_int, default=5, help="Number of slowest events to show.")
    report_parser.add_argument("--kind", help="Filter events by kind before summarizing.")
    report_parser.add_argument("--status", help="Filter events by status before summarizing.")
    report_parser.add_argument("--json", action="store_true", dest="as_json", help="Print the summary as JSON.")
    return parser


def run_file(
    python_file: str,
    *,
    no_console: bool = False,
    no_json: bool = False,
    output_dir: str | None = None,
    keep_history: bool = False,
    quiet: bool = False,
) -> int:
    """Execute a script and emit traces."""
    script_path = Path(python_file).resolve()
    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        return 1

    previous_config = get_config()
    reset_traces()
    set_config_overrides(
        enable_console=False if no_console else None,
        enable_json_export=False if no_json else None,
        output_dir=output_dir,
        overwrite_latest=False if keep_history else None,
        quiet=True if quiet else None,
    )
    configure(
        enable_console=not no_console,
        enable_json_export=not no_json,
        output_dir=output_dir or "traces",
        overwrite_latest=not keep_history,
        quiet=quiet,
    )

    original_argv = sys.argv[:]
    original_path = list(sys.path)
    sys.argv = [str(script_path)]
    sys.path.insert(0, str(script_path.parent))
    trace_output: Path | None = None
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        trace_output = flush()
        sys.argv = original_argv
        sys.path[:] = original_path
        clear_config_overrides()
        set_config(previous_config)

    if trace_output is not None and not quiet:
        print(f"Trace saved to: {trace_output}")
    return 0


def report_trace(
    json_trace_file: str,
    *,
    top: int = 5,
    kind: str | None = None,
    status: str | None = None,
    as_json: bool = False,
) -> int:
    """Read a trace file and print a summary report."""
    trace_path = Path(json_trace_file).resolve()
    if not trace_path.exists():
        print(f"Trace file not found: {trace_path}", file=sys.stderr)
        return 1

    summary = build_report_summary(trace_path, kind=kind, status=status, top=top)
    print(render_summary_json(summary) if as_json else render_summary(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_file(
            args.python_file,
            no_console=args.no_console,
            no_json=args.no_json,
            output_dir=args.output_dir,
            keep_history=args.keep_history,
            quiet=args.quiet,
        )
    if args.command == "report":
        return report_trace(
            args.json_trace_file,
            top=args.top,
            kind=args.kind,
            status=args.status,
            as_json=args.as_json,
        )
    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
