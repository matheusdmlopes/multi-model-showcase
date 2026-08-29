"""Tests for evidence verifier and manifest.json."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.verify_evidence import (
    REQUIRED_FIELDS,
    FORBIDDEN_FIELDS,
    verify_manifest,
    verify_evidence_file,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "evidence" / "manifest.json"


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
