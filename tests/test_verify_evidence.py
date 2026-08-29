"""Tests for evidence verifier and manifest.json."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.render_telemetry_summary import render_telemetry_summary
from scripts.verify_evidence import (
    REQUIRED_FIELDS,
    FORBIDDEN_FIELDS,
    TELEMETRY_REQUIRED_FIELDS,
    USAGE_REQUIRED_FIELDS,
    verify_evidence_bundle,
    verify_telemetry,
    verify_manifest,
    verify_evidence_file,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "evidence" / "manifest.json"
TELEMETRY_PATH = REPO_ROOT / "evidence" / "telemetry.json"


def telemetry_summary_record(
    model: str,
    worker_id: str,
    duration_seconds: float,
    usage: dict[str, int],
) -> dict[str, object]:
    return {
        "worker_id": worker_id,
        "tool": "delegate_agy",
        "model": model,
        "task_type": "implementation",
        "execution_mode": "accept_edits",
        "status": "succeeded",
        "returncode": 0,
        "duration_seconds": duration_seconds,
        "num_turns": 1,
        "usage": usage,
    }


def test_telemetry_summary_is_sorted_and_includes_totals():
    records = [
        telemetry_summary_record(
            "zeta-model",
            "agy_zeta",
            2.5,
            {
                "input_tokens": 20,
                "output_tokens": 3,
                "thinking_tokens": 4,
                "cache_read_tokens": 5,
                "total_tokens": 23,
            },
        ),
        telemetry_summary_record(
            "alpha-model",
            "agy_alpha",
            1.25,
            {
                "input_tokens": 10,
                "output_tokens": 2,
                "thinking_tokens": 3,
                "cache_read_tokens": 4,
                "total_tokens": 12,
            },
        ),
    ]

    assert render_telemetry_summary(records) == (
        "| Model | Worker | Execution mode | Duration (s) | Input | Output | Thinking | Cache read | Total |\n"
        "|---|---|---|---:|---:|---:|---:|---:|---:|\n"
        "| alpha-model | agy_alpha | accept_edits | 1.250 | 10 | 2 | 3 | 4 | 12 |\n"
        "| zeta-model | agy_zeta | accept_edits | 2.500 | 20 | 3 | 4 | 5 | 23 |\n"
        "| **Total** |  |  | 3.750 | 30 | 5 | 7 | 9 | 35 |"
    )


def test_readme_telemetry_summary_matches_generated_evidence():
    readme = (REPO_ROOT / "README.md").read_text()
    start = "<!-- telemetry-summary:start -->"
    end = "<!-- telemetry-summary:end -->"
    generated = render_telemetry_summary(json.loads(TELEMETRY_PATH.read_text()))
    block = readme.split(start, 1)[1].split(end, 1)[0].strip()
    assert block == generated


def valid_telemetry_record() -> dict[str, object]:
    return {
        "worker_id": "agy_telemetry_01",
        "tool": "delegate_agy",
        "model": "gemini-3.7-flash-low",
        "task_type": "simple",
        "execution_mode": "accept_edits",
        "status": "succeeded",
        "returncode": 0,
        "duration_seconds": 1.25,
        "num_turns": 1,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 2,
            "thinking_tokens": 3,
            "cache_read_tokens": 4,
            "total_tokens": 12,
        },
    }


def test_telemetry_constants_define_exact_allowlists():
    assert TELEMETRY_REQUIRED_FIELDS == {
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
    assert USAGE_REQUIRED_FIELDS == {
        "input_tokens",
        "output_tokens",
        "thinking_tokens",
        "cache_read_tokens",
        "total_tokens",
    }


def test_telemetry_accepts_complete_allowlisted_record():
    result = verify_telemetry([valid_telemetry_record()])
    assert result.is_valid, result.errors


def test_telemetry_rejects_raw_response_and_conversation_id():
    record = valid_telemetry_record()
    record["response"] = "private worker output"
    record["conversation_id"] = "private conversation"
    result = verify_telemetry([record])
    assert not result.is_valid
    assert any("forbidden" in error.lower() for error in result.errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_tokens", True),
        ("output_tokens", -1),
        ("thinking_tokens", 1.5),
        ("cache_read_tokens", "4"),
    ],
)
def test_telemetry_rejects_invalid_usage_values(field, value):
    record = valid_telemetry_record()
    record["usage"] = dict(record["usage"])
    record["usage"][field] = value
    result = verify_telemetry([record])
    assert not result.is_valid
    assert any(field in error for error in result.errors)


def test_telemetry_rejects_unknown_usage_fields():
    record = valid_telemetry_record()
    record["usage"] = dict(record["usage"])
    record["usage"]["owner_id"] = "private"
    result = verify_telemetry([record])
    assert not result.is_valid
    assert any("forbidden" in error.lower() for error in result.errors)


def valid_manifest_records(tmp_path: Path) -> list[dict[str, object]]:
    records = []
    for index in range(14):
        model = f"model-{index:02d}"
        file_name = f"test_{index:02d}.py"
        file_path = tmp_path / file_name
        file_path.write_text(f"# Model: {model}\ndef test_placeholder():\n    assert True\n")
        records.append(
            {
                "worker_id": f"agy_manifest_{index:02d}",
                "model": model,
                "status": "succeeded",
                "returncode": 0,
                "execution_mode": "accept_edits",
                "duration_seconds": float(index + 1),
                "num_turns": 1,
                "file": file_name,
                "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            }
        )
    return records


def valid_telemetry_records(
    manifest_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    records = []
    for manifest in manifest_records:
        record = valid_telemetry_record()
        record.update(
            {
                "worker_id": manifest["worker_id"],
                "model": manifest["model"],
                "execution_mode": manifest["execution_mode"],
                "status": manifest["status"],
                "returncode": manifest["returncode"],
                "duration_seconds": manifest["duration_seconds"],
                "num_turns": manifest["num_turns"],
            }
        )
        records.append(record)
    return records


def test_bundle_rejects_model_not_present_in_manifest(tmp_path):
    manifest = valid_manifest_records(tmp_path)
    telemetry = valid_telemetry_records(manifest)
    telemetry[0]["model"] = "model-not-in-manifest"
    result = verify_evidence_bundle(manifest, telemetry, repo_root=tmp_path)
    assert not result.is_valid
    assert any("model" in error.lower() for error in result.errors)


def test_bundle_rejects_mismatched_worker_metadata(tmp_path):
    manifest = valid_manifest_records(tmp_path)
    telemetry = valid_telemetry_records(manifest)
    telemetry[0]["duration_seconds"] = 99.0
    result = verify_evidence_bundle(manifest, telemetry, repo_root=tmp_path)
    assert not result.is_valid
    assert any("duration_seconds" in error for error in result.errors)


def test_manifest_file_exists():
    assert MANIFEST_PATH.is_file(), f"Manifest file not found at {MANIFEST_PATH}"


def test_manifest_passes_verifier():
    result = verify_evidence_file(MANIFEST_PATH, repo_root=REPO_ROOT)
    assert result.is_valid, f"Verification failed with errors: {result.errors}"
    assert len(result.records) == 14


def test_cli_verify_evidence_success():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_evidence.py"), str(MANIFEST_PATH)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"CLI verification failed: stdout={proc.stdout}, stderr={proc.stderr}"
    assert "14" in proc.stdout


def test_verifier_rejects_missing_required_field(tmp_path):
    bad_data = [
        {
            "worker_id": "agy_8d2f869a6aeb",
            "model": "gemini-3.7-flash-low",
            "status": "succeeded",
            "returncode": 0,
            "execution_mode": "accept_edits",
            "duration_seconds": 24.15,
            "num_turns": 1,
            "file": "tests/test_01_lowercase_by_gemini-3.7-flash-low.py",
            # sha256 missing
        }
    ]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad_data))
    result = verify_evidence_file(manifest, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("missing required field" in err.lower() for err in result.errors)


def test_verifier_rejects_forbidden_sensitive_fields(tmp_path):
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    bad_data = list(data)
    bad_data[0] = dict(bad_data[0])
    bad_data[0]["prompt"] = "secret prompt"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad_data))
    result = verify_evidence_file(manifest, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("forbidden field" in err.lower() for err in result.errors)


def test_verifier_rejects_unexpected_fields(tmp_path):
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    bad_data = list(data)
    bad_data[0] = dict(bad_data[0])
    bad_data[0]["unexpected_metadata"] = "must not be published"
    result = verify_manifest(bad_data, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("unexpected field" in err.lower() for err in result.errors)


def test_verifier_rejects_duplicate_models(tmp_path):
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    bad_data = list(data)
    bad_data[1] = dict(bad_data[1])
    bad_data[1]["model"] = bad_data[0]["model"]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad_data))
    result = verify_evidence_file(manifest, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("duplicate model" in err.lower() for err in result.errors)


def test_verifier_rejects_sha_mismatch(tmp_path):
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    bad_data = list(data)
    bad_data[0] = dict(bad_data[0])
    bad_data[0]["sha256"] = "0" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad_data))
    result = verify_evidence_file(manifest, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("sha256 mismatch" in err.lower() for err in result.errors)


def test_verifier_rejects_bad_status_or_returncode(tmp_path):
    with open(MANIFEST_PATH) as f:
        data = json.load(f)
    bad_data = list(data)
    bad_data[0] = dict(bad_data[0])
    bad_data[0]["status"] = "failed"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(bad_data))
    result = verify_evidence_file(manifest, repo_root=REPO_ROOT)
    assert not result.is_valid
    assert any("status" in err.lower() for err in result.errors)


def test_verifier_rejects_wrong_header(tmp_path):
    fake_file = tmp_path / "test_fake.py"
    fake_file.write_text("# Model: wrong-model\ndef test_dummy(): pass\n")
    import hashlib
    sha = hashlib.sha256(fake_file.read_bytes()).hexdigest()

    records = [
        {
            "worker_id": f"agy_fake_{i}",
            "model": f"model-{i}",
            "status": "succeeded",
            "returncode": 0,
            "execution_mode": "accept_edits",
            "duration_seconds": 1.0,
            "num_turns": 1,
            "file": "test_fake.py" if i == 0 else f"test_{i}.py",
            "sha256": sha if i == 0 else "abc",
        }
        for i in range(14)
    ]
    result = verify_manifest(records, repo_root=tmp_path)
    assert not result.is_valid
    assert any("header" in err.lower() or "mismatch" in err.lower() for err in result.errors)
