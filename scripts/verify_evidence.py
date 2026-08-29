#!/usr/bin/env python3
"""Verification script for delegate_agy evidence manifest.

Validates:
- Manifest JSON schema & required fields
- Sanitization (no forbidden/sensitive keys)
- Uniqueness across all 14 models, files, and worker IDs
- Status succeeded, returncode 0, execution_mode accept_edits
- Existence of test files relative to repo root
- Match of SHA-256 digests
- Match of '# Model: <model>' headers in test files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

EXPECTED_COUNT = 14

REQUIRED_FIELDS = {
    "worker_id",
    "model",
    "status",
    "returncode",
    "execution_mode",
    "duration_seconds",
    "num_turns",
    "file",
    "sha256",
}

FORBIDDEN_FIELDS = {
    "prompt",
    "prompts",
    "response",
    "responses",
    "conversation_id",
    "workdir",
    "stdout_path",
    "stderr_path",
    "owner_id",
    "usage",
    "email",
    "token",
    "tokens",
    "secret",
    "secrets",
    "password",
    "api_key",
}

TELEMETRY_REQUIRED_FIELDS = {
    "worker_id",
    "tool",
    "model",
    "task_type",
    "execution_mode",
    "status",
    "returncode",
    "duration_seconds",
    "num_turns",
    "usage",
}

USAGE_REQUIRED_FIELDS = {
    "input_tokens",
    "output_tokens",
    "thinking_tokens",
    "cache_read_tokens",
    "total_tokens",
}

TELEMETRY_FORBIDDEN_FIELDS = FORBIDDEN_FIELDS - {"usage"}

CROSS_FILE_EQUAL_FIELDS = {
    "worker_id",
    "model",
    "execution_mode",
    "status",
    "returncode",
    "duration_seconds",
    "num_turns",
}


@dataclass
class VerificationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)


def _append_field_allowlist_errors(
    errors: list[str],
    prefix: str,
    actual_fields: set[str],
    required_fields: set[str],
    forbidden_fields: set[str],
) -> None:
    """Append missing, unexpected, and forbidden field errors."""
    missing = required_fields - actual_fields
    if missing:
        errors.append(
            f"{prefix}: missing required field(s): {', '.join(sorted(missing))}"
        )

    forbidden_present = actual_fields & forbidden_fields
    if forbidden_present:
        errors.append(
            f"{prefix}: contains forbidden field(s): {', '.join(sorted(forbidden_present))}"
        )

    unexpected = actual_fields - required_fields - forbidden_fields
    if unexpected:
        errors.append(
            f"{prefix}: contains unexpected field(s): {', '.join(sorted(unexpected))}"
        )


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_negative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def verify_telemetry(
    records: Any,
    *,
    expected_count: int | None = None,
) -> VerificationResult:
    """Verify sanitized in-memory delegate_agy telemetry records."""
    if not isinstance(records, list):
        return VerificationResult(
            is_valid=False,
            errors=[f"Telemetry content must be a JSON list, got {type(records).__name__}"],
            records=[],
        )

    errors: list[str] = []
    if expected_count is not None and len(records) != expected_count:
        errors.append(f"Expected exactly {expected_count} telemetry records, found {len(records)}")

    seen_workers: set[str] = set()
    seen_models: set[str] = set()

    for index, item in enumerate(records):
        prefix = f"Telemetry record [{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: entry must be a dictionary, got {type(item).__name__}")
            continue

        worker_id = item.get("worker_id")
        if _is_non_empty_string(worker_id):
            prefix = f"{prefix} ({worker_id})"
            if worker_id in seen_workers:
                errors.append(f"{prefix}: duplicate worker_id '{worker_id}'")
            seen_workers.add(worker_id)
        else:
            errors.append(f"{prefix}: worker_id must be a non-empty string")

        _append_field_allowlist_errors(
            errors,
            prefix,
            set(item),
            TELEMETRY_REQUIRED_FIELDS,
            TELEMETRY_FORBIDDEN_FIELDS,
        )

        model = item.get("model")
        if _is_non_empty_string(model):
            if model in seen_models:
                errors.append(f"{prefix}: duplicate model '{model}'")
            seen_models.add(model)
        else:
            errors.append(f"{prefix}: model must be a non-empty string")

        if item.get("tool") != "delegate_agy":
            errors.append(f"{prefix}: tool must be 'delegate_agy'")
        if not _is_non_empty_string(item.get("task_type")):
            errors.append(f"{prefix}: task_type must be a non-empty string")
        if item.get("execution_mode") != "accept_edits":
            errors.append(f"{prefix}: execution_mode must be 'accept_edits'")
        if item.get("status") != "succeeded":
            errors.append(f"{prefix}: status must be 'succeeded'")
        if item.get("returncode") != 0 or isinstance(item.get("returncode"), bool):
            errors.append(f"{prefix}: returncode must be integer 0")

        duration = item.get("duration_seconds")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration < 0
        ):
            errors.append(f"{prefix}: duration_seconds must be a non-negative finite number")

        num_turns = item.get("num_turns")
        if not isinstance(num_turns, int) or isinstance(num_turns, bool) or num_turns <= 0:
            errors.append(f"{prefix}: num_turns must be a positive integer")

        usage = item.get("usage")
        if not isinstance(usage, dict):
            errors.append(f"{prefix}: usage must be a dictionary")
            continue

        _append_field_allowlist_errors(
            errors,
            f"{prefix}: usage",
            set(usage),
            USAGE_REQUIRED_FIELDS,
            TELEMETRY_FORBIDDEN_FIELDS,
        )
        for field_name in USAGE_REQUIRED_FIELDS:
            value = usage.get(field_name)
            if not _is_non_negative_integer(value):
                errors.append(
                    f"{prefix}: usage.{field_name} must be a non-negative integer"
                )

    return VerificationResult(
        is_valid=not errors,
        errors=errors,
        records=records,
    )


def verify_manifest(
    records: Any,
    repo_root: Path | str | None = None,
) -> VerificationResult:
    """Verify in-memory manifest records against constraints and files on disk."""
    errors: list[str] = []

    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)

    if not isinstance(records, list):
        return VerificationResult(
            is_valid=False,
            errors=[f"Manifest content must be a JSON list, got {type(records).__name__}"],
            records=[],
        )

    if len(records) != EXPECTED_COUNT:
        errors.append(
            f"Expected exactly {EXPECTED_COUNT} records, found {len(records)}"
        )

    seen_workers: set[str] = set()
    seen_models: set[str] = set()
    seen_files: set[str] = set()

    for idx, item in enumerate(records):
        prefix = f"Record [{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: entry must be a dictionary, got {type(item).__name__}")
            continue

        worker_id = item.get("worker_id", f"<unknown-{idx}>")
        prefix = f"Record [{idx}] ({worker_id})"

        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if f not in item or item[f] is None]
        if missing:
            errors.append(f"{prefix}: missing required field(s): {', '.join(sorted(missing))}")

        unexpected = set(item) - REQUIRED_FIELDS - FORBIDDEN_FIELDS
        if unexpected:
            errors.append(
                f"{prefix}: contains unexpected field(s): {', '.join(sorted(unexpected))}"
            )

        # Check forbidden fields
        forbidden_present = [f for f in FORBIDDEN_FIELDS if f in item]
        if forbidden_present:
            errors.append(
                f"{prefix}: contains forbidden field(s): {', '.join(sorted(forbidden_present))}"
            )

        model = item.get("model")
        file_path_str = item.get("file")
        status = item.get("status")
        returncode = item.get("returncode")
        execution_mode = item.get("execution_mode")
        expected_sha = item.get("sha256")

        # Uniqueness checks
        if worker_id in seen_workers:
            errors.append(f"{prefix}: duplicate worker_id '{worker_id}'")
        seen_workers.add(worker_id)

        if model:
            if model in seen_models:
                errors.append(f"{prefix}: duplicate model '{model}'")
            seen_models.add(model)

        if file_path_str:
            if file_path_str in seen_files:
                errors.append(f"{prefix}: duplicate file path '{file_path_str}'")
            seen_files.add(file_path_str)

        # Status / Returncode / Mode checks
        if status != "succeeded":
            errors.append(f"{prefix}: status is '{status}', expected 'succeeded'")

        if returncode != 0:
            errors.append(f"{prefix}: returncode is {returncode}, expected 0")

        if execution_mode != "accept_edits":
            errors.append(
                f"{prefix}: execution_mode is '{execution_mode}', expected 'accept_edits'"
            )

        # File validation on disk
        if file_path_str:
            rel_p = Path(file_path_str)
            if rel_p.is_absolute():
                errors.append(f"{prefix}: file path '{file_path_str}' must be relative")
                continue

            full_p = (repo_root / rel_p).resolve()
            try:
                # Ensure the resolved file stays inside repo_root
                full_p.relative_to(repo_root.resolve())
            except ValueError:
                errors.append(f"{prefix}: file '{file_path_str}' escapes repo root")
                continue

            if not full_p.is_file():
                errors.append(f"{prefix}: referenced file does not exist: {file_path_str}")
                continue

            # Read file bytes
            try:
                content = full_p.read_bytes()
            except OSError as e:
                errors.append(f"{prefix}: could not read file '{file_path_str}': {e}")
                continue

            # SHA-256 check
            actual_sha = hashlib.sha256(content).hexdigest()
            if expected_sha and actual_sha.lower() != str(expected_sha).lower():
                errors.append(
                    f"{prefix}: sha256 mismatch for {file_path_str}. "
                    f"Expected {expected_sha}, got {actual_sha}"
                )

            # Header check: line 1 must match '# Model: <model>'
            try:
                text_content = content.decode("utf-8")
                first_line = text_content.splitlines()[0].strip() if text_content else ""
                expected_header = f"# Model: {model}"
                if model and first_line != expected_header:
                    errors.append(
                        f"{prefix}: header mismatch in {file_path_str}. "
                        f"Expected line 1 '{expected_header}', got '{first_line}'"
                    )
            except UnicodeDecodeError as e:
                errors.append(f"{prefix}: file '{file_path_str}' is not valid UTF-8: {e}")

    return VerificationResult(
        is_valid=(len(errors) == 0),
        errors=errors,
        records=records if isinstance(records, list) else [],
    )


def verify_evidence_file(
    manifest_path: Path | str,
    repo_root: Path | str | None = None,
) -> VerificationResult:
    """Load manifest from JSON file and verify."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        return VerificationResult(
            is_valid=False,
            errors=[f"Manifest file not found: {manifest_path}"],
            records=[],
        )

    if repo_root is None:
        # Default repo_root to manifest's parent directory's parent (e.g. evidence/../)
        repo_root = manifest_path.resolve().parent.parent

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return VerificationResult(
            is_valid=False,
            errors=[f"Failed to parse JSON from {manifest_path}: {e}"],
            records=[],
        )

    return verify_manifest(data, repo_root=repo_root)


def verify_telemetry_file(telemetry_path: Path | str) -> VerificationResult:
    """Load telemetry from a JSON file and verify its public schema."""
    telemetry_path = Path(telemetry_path)
    if not telemetry_path.is_file():
        return VerificationResult(
            is_valid=False,
            errors=[f"Telemetry file not found: {telemetry_path}"],
            records=[],
        )

    try:
        with open(telemetry_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except Exception as error:
        return VerificationResult(
            is_valid=False,
            errors=[f"Failed to parse JSON from {telemetry_path}: {error}"],
            records=[],
        )

    return verify_telemetry(data, expected_count=EXPECTED_COUNT)


def verify_evidence_bundle(
    manifest_records: Any,
    telemetry_records: Any,
    *,
    repo_root: Path | str,
) -> VerificationResult:
    """Verify manifest and telemetry records together as one evidence bundle."""
    manifest_result = verify_manifest(manifest_records, repo_root=repo_root)
    telemetry_result = verify_telemetry(telemetry_records, expected_count=EXPECTED_COUNT)
    errors = [*manifest_result.errors, *telemetry_result.errors]

    if not isinstance(manifest_records, list) or not isinstance(telemetry_records, list):
        return VerificationResult(
            is_valid=False,
            errors=errors,
            records=manifest_result.records,
        )

    manifest_by_model = {
        record.get("model"): record
        for record in manifest_records
        if isinstance(record, dict) and _is_non_empty_string(record.get("model"))
    }
    telemetry_by_model = {
        record.get("model"): record
        for record in telemetry_records
        if isinstance(record, dict) and _is_non_empty_string(record.get("model"))
    }

    manifest_models = set(manifest_by_model)
    telemetry_models = set(telemetry_by_model)
    for model in sorted(manifest_models - telemetry_models):
        errors.append(f"Cross-file mismatch: manifest model '{model}' is missing from telemetry")
    for model in sorted(telemetry_models - manifest_models):
        errors.append(f"Cross-file mismatch: telemetry model '{model}' is missing from manifest")

    for model in sorted(manifest_models & telemetry_models):
        manifest_record = manifest_by_model[model]
        telemetry_record = telemetry_by_model[model]
        for field_name in sorted(CROSS_FILE_EQUAL_FIELDS):
            if manifest_record.get(field_name) != telemetry_record.get(field_name):
                errors.append(
                    f"Cross-file mismatch for model '{model}': {field_name} differs"
                )

    return VerificationResult(
        is_valid=not errors,
        errors=errors,
        records=manifest_result.records,
    )


def _print_errors(label: str, errors: list[str]) -> None:
    print(f"FAILED: {label} ({len(errors)} error(s)):", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)


def _usage_totals(records: list[dict[str, Any]]) -> dict[str, int]:
    """Return aggregate usage counters from telemetry already validated by the caller."""
    return {
        field_name: sum(record["usage"][field_name] for record in records)
        for field_name in sorted(USAGE_REQUIRED_FIELDS)
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify delegate_agy manifest and telemetry evidence integrity."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="evidence/manifest.json",
        help="Path to manifest.json (default: evidence/manifest.json)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Path to repository root (defaults to inferred root)",
    )
    parser.add_argument(
        "--telemetry",
        default=None,
        help="Path to telemetry.json (defaults to the manifest sibling)",
    )

    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    telemetry_path = Path(args.telemetry) if args.telemetry else manifest_path.with_name("telemetry.json")
    repo_root = Path(args.repo_root) if args.repo_root else None

    manifest_result = verify_evidence_file(manifest_path, repo_root=repo_root)
    telemetry_result = verify_telemetry_file(telemetry_path)
    if not manifest_result.is_valid or not telemetry_result.is_valid:
        if not manifest_result.is_valid:
            _print_errors("Manifest validation failed", manifest_result.errors)
        if not telemetry_result.is_valid:
            _print_errors("Telemetry validation failed", telemetry_result.errors)
        return 1

    bundle_repo_root = repo_root or manifest_path.resolve().parent.parent
    result = verify_evidence_bundle(
        manifest_result.records,
        telemetry_result.records,
        repo_root=bundle_repo_root,
    )

    if not result.is_valid:
        _print_errors("Cross-file evidence validation failed", result.errors)
        return 1

    totals = _usage_totals(telemetry_result.records)
    print(
        f"SUCCESS: All {len(result.records)} manifest records and "
        f"{len(telemetry_result.records)} telemetry records verified successfully.\n"
        f"Manifest: {manifest_path}\n"
        f"Telemetry: {telemetry_path}\n"
        f"Verified: status=succeeded, returncode=0, execution_mode=accept_edits, valid headers & sha256.\n"
        "Aggregate usage: "
        + ", ".join(f"{field_name}={totals[field_name]}" for field_name in sorted(totals))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
