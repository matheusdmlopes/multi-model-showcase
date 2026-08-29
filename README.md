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
  manifest.json     Worker-to-model-to-test SHA-256 integrity records
  telemetry.json    Sanitized per-call delegate_agy usage telemetry
scripts/
  verify_evidence.py           Stdlib-only evidence-bundle verifier
  render_telemetry_summary.py  Deterministic Markdown telemetry renderer
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

Expected result: **14 test files, 90 showcase tests passed** (plus 22 verifier and documentation tests, 112 total).

## Evidence & Verification

Each test file was generated via an autonomous `delegate_agy(spawn)` worker in `accept_edits` mode. The integrity link between each model, worker, and test file is published in [`evidence/manifest.json`](evidence/manifest.json) containing:
- `worker_id`
- `model`
- `status` (`succeeded`)
- `returncode` (`0`)
- `execution_mode` (`accept_edits`)
- `duration_seconds`
- `num_turns`
- relative `file` path
- current `sha256` digest

To verify the manifest, telemetry, and file integrity independently with standard library Python:

```bash
python scripts/verify_evidence.py evidence/manifest.json --telemetry evidence/telemetry.json
```

## Per-call quota telemetry

The table below is generated from [`evidence/telemetry.json`](evidence/telemetry.json), a sanitized allowlist of values returned by individual `delegate_agy` worker results. It does not contain prompts, worker responses, conversation IDs, local paths, or credentials. The telemetry is separate from the manifest because it records per-call usage counters rather than file-integrity links.

<!-- telemetry-summary:start -->
| Model | Worker | Execution mode | Duration (s) | Input | Output | Thinking | Cache read | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|
| claude-opus-4-6-thinking | agy_fa5e04781beb | accept_edits | 46.732 | 25019 | 2620 | 0 | 113693 | 27639 |
| claude-sonnet-4-6 | agy_72df668ba883 | accept_edits | 64.758 | 30155 | 3623 | 0 | 180868 | 33778 |
| gemini-3.1-pro-high | agy_1b4ed237e6d8 | accept_edits | 45.160 | 51860 | 3414 | 1785 | 113376 | 55274 |
| gemini-3.1-pro-low | agy_bb388d37151c | accept_edits | 37.718 | 49545 | 2312 | 1214 | 105081 | 51857 |
| gemini-3.5-flash-high | agy_e35bf642ced5 | accept_edits | 39.631 | 104283 | 13545 | 8203 | 467803 | 117828 |
| gemini-3.5-flash-low | agy_f147f4348122 | accept_edits | 15.055 | 83844 | 3030 | 1327 | 129865 | 86874 |
| gemini-3.5-flash-medium | agy_1f841dac587a | accept_edits | 25.553 | 121908 | 9373 | 6623 | 186980 | 131281 |
| gemini-3.6-flash-high | agy_01a4e9cc6450 | accept_edits | 14.542 | 52397 | 4859 | 3029 | 150427 | 57256 |
| gemini-3.6-flash-low | agy_5e22823134af | accept_edits | 11.791 | 52690 | 1551 | 0 | 109691 | 54241 |
| gemini-3.6-flash-medium | agy_c4d525a2cfa8 | accept_edits | 27.651 | 124119 | 8581 | 5258 | 337657 | 132700 |
| gemini-3.7-flash-high | agy_bb62e9772f26 | accept_edits | 34.253 | 80630 | 8056 | 4826 | 207345 | 88686 |
| gemini-3.7-flash-low | agy_e2b87daf0272 | accept_edits | 13.970 | 95827 | 1318 | 0 | 56820 | 97145 |
| gemini-3.7-flash-medium | agy_e960d39601c1 | accept_edits | 38.279 | 80293 | 6772 | 3331 | 215534 | 87065 |
| gpt-oss-120b-medium | agy_e86dc47e3b0f | accept_edits | 19.105 | 120064 | 1953 | 0 | 0 | 122017 |
| **Total** |  |  | 434.199 | 1072634 | 71007 | 35596 | 2375140 | 1143641 |
<!-- telemetry-summary:end -->

Regenerate the table with:

```bash
python scripts/render_telemetry_summary.py evidence/telemetry.json
```

The plugin that drove the spawns is [`delegate_agy`](https://github.com/matheusdmlopes/hermes-delegate-agy).
