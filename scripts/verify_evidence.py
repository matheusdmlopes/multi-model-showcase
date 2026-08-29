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


@dataclass
class VerificationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify delegate_agy evidence manifest integrity."
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

    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    repo_root = Path(args.repo_root) if args.repo_root else None

    result = verify_evidence_file(manifest_path, repo_root=repo_root)

    if not result.is_valid:
        print(f"FAILED: Evidence verification failed ({len(result.errors)} error(s)):", file=sys.stderr)
        for err in result.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"SUCCESS: All {len(result.records)} worker evidence records verified successfully.\n"
        f"Manifest: {manifest_path}\n"
        f"Verified: status=succeeded, returncode=0, execution_mode=accept_edits, valid headers & sha256."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
