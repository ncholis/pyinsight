from __future__ import annotations

import json
import os
from pathlib import Path

from pyinsight.cli import main


def test_cli_run_and_report(tmp_path, capsys) -> None:
    script = tmp_path / "demo.py"
    script.write_text(
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
