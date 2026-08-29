# multi-model-showcase

A mini project built by Antigravity models through the
[`delegate_agy`](https://github.com/matheusdmlopes/hermes-delegate-agy)
plugin of [Hermes Agent](https://github.com/NousResearch/hermes-agent).

The goal: demonstrate that individual `delegate_agy(spawn)` invocations can drive each
of the 14 Antigravity-backed models with per-worker model routing and autonomous `accept_edits`
execution to collaborate on one project. The base library (`wordstats`) and each test file
were written by different models operating on distinct behavioral contracts.

> **Note on scope**: This showcase validates **14 individual worker spawns** and **`accept_edits` execution mode** across multiple model families. It does not claim to demonstrate or benchmark batch `tasks:[...]` execution.

## What is here

```
src/wordstats/
  __init__.py       word_frequencies() — base library, written by gemini-3.7-flash-high
  cli.py            stdin → sorted frequencies, written by gemini-3.7-flash-high
tests/
  test_01_lowercase_by_gemini-3.7-flash-low.py
  test_02_punctuation_by_gemini-3.7-flash-medium.py
  test_03_sorting_by_gemini-3.7-flash-high.py
  test_04_empty_by_gemini-3.6-flash-low.py
  test_05_unicode_by_gemini-3.6-flash-medium.py
  test_06_hyphenated_by_gemini-3.6-flash-high.py
  test_07_numbers_by_gemini-3.5-flash-low.py
  test_08_determinism_by_gemini-3.5-flash-medium.py
  test_09_long_text_by_gemini-3.5-flash-high.py
  test_10_cli_format_by_gemini-3.1-pro-high.py
  test_11_quotes_by_gemini-3.1-pro-low.py
  test_12_does_not_mutate_by_claude-sonnet-4-6.py
  test_13_signature_by_claude-opus-4-6-thinking.py
  test_14_idempotent_keys_by_gpt-oss-120b-medium.py
evidence/
  manifest.json     Sanitized worker execution metadata and SHA-256 hashes
scripts/
  verify_evidence.py Stdlib-only integrity verifier for manifest and files
```

Every showcase test file targets a **different behavioural aspect** of
`wordstats`, so the files are independent — no ordering, no shared
state, no fixtures.

## Build matrix

| Model                       | Family     | Test file                                             | What it asserts                                     |
|-----------------------------|------------|-------------------------------------------------------|-----------------------------------------------------|
| gemini-3.7-flash-low        | Gemini 3.7 | `test_01_lowercase_by_gemini-3.7-flash-low.py`        | All keys are lowercased before counting             |
| gemini-3.7-flash-medium     | Gemini 3.7 | `test_02_punctuation_by_gemini-3.7-flash-medium.py`  | Punctuation is stripped exactly per the contract    |
| gemini-3.7-flash-high       | Gemini 3.7 | `test_03_sorting_by_gemini-3.7-flash-high.py`          | CLI sort order: count desc, then word asc           |
| gemini-3.6-flash-low        | Gemini 3.6 | `test_04_empty_by_gemini-3.6-flash-low.py`            | Empty / whitespace-only input → empty dict          |
| gemini-3.6-flash-medium     | Gemini 3.6 | `test_05_unicode_by_gemini-3.6-flash-medium.py`        | Non-ASCII tokens (accents, CJK) are kept verbatim   |
| gemini-3.6-flash-high       | Gemini 3.6 | `test_06_hyphenated_by_gemini-3.6-flash-high.py`       | Hyphenated tokens treated as single words           |
| gemini-3.5-flash-low        | Gemini 3.5 | `test_07_numbers_by_gemini-3.5-flash-low.py`          | Tokens with digits are counted like other tokens    |
| gemini-3.5-flash-medium     | Gemini 3.5 | `test_08_determinism_by_gemini-3.5-flash-medium.py`   | Calling word_frequencies twice is deterministic     |
| gemini-3.5-flash-high       | Gemini 3.5 | `test_09_long_text_by_gemini-3.5-flash-high.py`       | Handles large input without crashing                |
| gemini-3.1-pro-high         | Gemini Pro | `test_10_cli_format_by_gemini-3.1-pro-high.py`        | CLI main() prints "word\tcount" format              |
| gemini-3.1-pro-low          | Gemini Pro | `test_11_quotes_by_gemini-3.1-pro-low.py`             | Curly quotes are stripped like ASCII quotes         |
| claude-sonnet-4-6           | Claude     | `test_12_does_not_mutate_by_claude-sonnet-4-6.py`  | Returned dict is a fresh object each call           |
| claude-opus-4-6-thinking    | Claude     | `test_13_signature_by_claude-opus-4-6-thinking.py`    | Type signature is `dict[str, int]` (per __init__)   |
| gpt-oss-120b-medium         | GPT-OSS    | `test_14_idempotent_keys_by_gpt-oss-120b-medium.py`  | Same input → same keys and same counts              |

## Installation & Testing

Install editable package with test dependencies:

```bash
python -m pip install -e '.[test]'
```

Run test suite:

```bash
python -m pytest -v
```

Expected result: **14 test files, 58 showcase tests passed** (plus 10 verifier tests for the manifest, 68 total).

## Evidence & Verification

Each test file was generated via an autonomous `delegate_agy(spawn)` worker in `accept_edits` mode. A sanitized record of the 14 worker executions is published in [`evidence/manifest.json`](evidence/manifest.json) containing:
- `worker_id`
- `model`
- `status` (`succeeded`)
- `returncode` (`0`)
- `execution_mode` (`accept_edits`)
- `duration_seconds`
- `num_turns`
- relative `file` path
- current `sha256` digest

To verify the manifest and file integrity independently with standard library Python:

```bash
python scripts/verify_evidence.py
```

The plugin that drove the spawns is [`delegate_agy`](https://github.com/matheusdmlopes/hermes-delegate-agy).
