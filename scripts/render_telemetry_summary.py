#!/usr/bin/env python3
"""Render a stable public Markdown summary from sanitized telemetry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    from .verify_evidence import verify_telemetry_file
except ImportError:
    from verify_evidence import verify_telemetry_file


def render_telemetry_summary(records: list[dict[str, object]]) -> str:
    """Return a stable Markdown quota table from already validated telemetry."""
    lines = [
        "| Model | Worker | Execution mode | Duration (s) | Input | Output | Thinking | Cache read | Total |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    totals = {
        "duration_seconds": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "cache_read_tokens": 0,
        "total_tokens": 0,
    }

    for record in sorted(records, key=lambda item: str(item["model"])):
        usage = record["usage"]
        if not isinstance(usage, dict):
            raise ValueError("Telemetry usage must be a dictionary")
        duration = record["duration_seconds"]
        if not isinstance(duration, (int, float)):
            raise ValueError("Telemetry duration_seconds must be numeric")

        totals["duration_seconds"] += duration
        for field_name in (
            "input_tokens",
            "output_tokens",
            "thinking_tokens",
            "cache_read_tokens",
            "total_tokens",
        ):
            value = usage[field_name]
            if not isinstance(value, int):
                raise ValueError(f"Telemetry usage.{field_name} must be an integer")
            totals[field_name] += value

        lines.append(
            "| {model} | {worker_id} | {execution_mode} | {duration:.3f} | "
            "{input_tokens} | {output_tokens} | {thinking_tokens} | "
            "{cache_read_tokens} | {total_tokens} |".format(
                model=record["model"],
                worker_id=record["worker_id"],
                execution_mode=record["execution_mode"],
                duration=duration,
                **usage,
            )
        )

    lines.append(
        "| **Total** |  |  | {duration_seconds:.3f} | {input_tokens} | "
        "{output_tokens} | {thinking_tokens} | {cache_read_tokens} | {total_tokens} |".format(
            **totals
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a deterministic Markdown quota table from sanitized telemetry."
    )
    parser.add_argument(
        "telemetry",
        nargs="?",
        default="evidence/telemetry.json",
        help="Path to telemetry.json (default: evidence/telemetry.json)",
    )
    args = parser.parse_args(argv)

    result = verify_telemetry_file(Path(args.telemetry))
    if not result.is_valid:
        print("FAILED: Telemetry rendering validation failed:", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(render_telemetry_summary(result.records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
