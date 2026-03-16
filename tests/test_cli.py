from __future__ import annotations

import json
import os
import time
from pathlib import Path

from pyinsight.cli import main


def write_demo_script(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "from pyinsight import trace",
                "",
                "@trace",
                "def main_pipeline() -> None:",
                "    pass",
                "",
                "main_pipeline()",
            ]
        ),
        encoding="utf-8",
    )


def write_report_fixture(path: Path) -> None:
    payload = {
        "created_at": "2026-03-17T00:00:00+00:00",
        "run": {"event_count": 4, "root_event_count": 2},
        "total_duration_ms": 100.0,
        "events": [
            {
                "event_id": "1",
                "parent_id": None,
                "name": "pipeline",
                "kind": "trace",
                "start_ns": 0,
                "end_ns": 100,
                "duration_ms": 100.0,
                "status": "ok",
                "metadata": {},
            },
            {
                "event_id": "2",
                "parent_id": "1",
                "name": "normalize",
                "kind": "span",
                "start_ns": 10,
                "end_ns": 60,
                "duration_ms": 50.0,
                "status": "ok",
                "metadata": {"slow": True},
            },
            {
                "event_id": "3",
                "parent_id": "1",
                "name": "save",
                "kind": "trace",
                "start_ns": 60,
                "end_ns": 90,
                "duration_ms": 30.0,
                "status": "error",
                "metadata": {"exception_type": "ValueError", "exception_message": "write failed"},
            },
            {
                "event_id": "4",
                "parent_id": None,
                "name": "cleanup",
                "kind": "trace",
                "start_ns": 100,
                "end_ns": 110,
                "duration_ms": 10.0,
                "status": "ok",
                "metadata": {},
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cli_run_and_report(tmp_path, capsys) -> None:
    script = tmp_path / "demo.py"
    write_demo_script(script)

    cwd = Path.cwd()
    try:
        output_dir = tmp_path / "work"
        output_dir.mkdir()
        os.chdir(output_dir)
        assert main(["run", str(script)]) == 0
        trace_file = output_dir / "traces" / "latest.json"
        assert trace_file.exists()

        payload = json.loads(trace_file.read_text(encoding="utf-8"))
        assert payload["events"][0]["name"] == "main_pipeline()"

        assert main(["report", str(trace_file)]) == 0
        stdout = capsys.readouterr().out
        assert "Total events: 1" in stdout
        assert "Top slowest events:" in stdout
    finally:
        os.chdir(cwd)


def test_cli_run_flags_disable_console_and_set_output_dir(tmp_path, capsys) -> None:
    script = tmp_path / "demo.py"
    write_demo_script(script)

    cwd = Path.cwd()
    try:
        workdir = tmp_path / "work"
        workdir.mkdir()
        os.chdir(workdir)
        custom_output = workdir / "custom_traces"

        assert main(["run", str(script), "--no-console", "--output-dir", str(custom_output), "--quiet"]) == 0
        stdout = capsys.readouterr().out
        assert "main_pipeline()" not in stdout
        assert (custom_output / "latest.json").exists()
    finally:
        os.chdir(cwd)


def test_cli_run_keep_history_creates_timestamped_files(tmp_path) -> None:
    script = tmp_path / "demo.py"
    write_demo_script(script)

    cwd = Path.cwd()
    try:
        workdir = tmp_path / "work"
        workdir.mkdir()
        os.chdir(workdir)
        assert main(["run", str(script), "--keep-history", "--no-console", "--quiet"]) == 0
        time.sleep(0.01)
        assert main(["run", str(script), "--keep-history", "--no-console", "--quiet"]) == 0

        trace_files = sorted((workdir / "traces").glob("trace-*.json"))
        assert len(trace_files) == 2
    finally:
        os.chdir(cwd)


def test_cli_report_supports_top_option(tmp_path, capsys) -> None:
    trace_file = tmp_path / "trace.json"
    write_report_fixture(trace_file)

    assert main(["report", str(trace_file), "--top", "2"]) == 0
    stdout = capsys.readouterr().out

    assert "Average duration: 47.50ms" in stdout
    assert "- pipeline 100.00ms" in stdout
    assert "- normalize 50.00ms [SLOW]" in stdout
    assert "- save 30.00ms" not in stdout


def test_cli_report_supports_filters_and_json_output(tmp_path, capsys) -> None:
    trace_file = tmp_path / "trace.json"
    write_report_fixture(trace_file)

    assert main(["report", str(trace_file), "--kind", "span", "--status", "ok", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["total_events"] == 1
    assert payload["event_counts_by_kind"] == {"span": 1}
    assert payload["slow_events"] == 1


def test_cli_report_supports_status_filter(tmp_path, capsys) -> None:
    trace_file = tmp_path / "trace.json"
    write_report_fixture(trace_file)

    assert main(["report", str(trace_file), "--status", "error"]) == 0
    stdout = capsys.readouterr().out

    assert "Filters: status=error" in stdout
    assert "Total events: 1" in stdout
    assert "Error events: 1" in stdout
    assert "- save 30.00ms [ERROR]" in stdout
