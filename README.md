# multi-model-showcase

A mini project built **entirely** by Antigravity models through the
[`delegate_agy`](https://github.com/matheusdmlopes/hermes-delegate-agy)
plugin of [Hermes Agent](https://github.com/NousResearch/hermes-agent).

The goal: prove that a single `delegate_agy` invocation can drive any
of the 14 Antigravity-backed models and have them collaborate on one
project. The base library (`wordstats`) and each test file were each
written by a different model working from a different prompt.

## What is here

```
src/wordstats/
  __init__.py       word_frequencies() — base library, written by gemini-3.7-flash-high
  cli.py            stdin → sorted frequencies, written by gemini-3.7-flash-high
tests/
  test_01_lowercase.py              — gemini-3.7-flash-low
  test_02_punctuation.py            — gemini-3.7-flash-medium
  test_03_sorting.py                — gemini-3.7-flash-high
  test_04_empty.py                  — gemini-3.7-flash-low (different prompt)
  ...
  test_14_<aspect>.py               — gpt-oss-120b-medium
```

Every test file targets a **different behavioural aspect** of
`wordstats`, so the files are independent — no ordering, no shared
state, no fixtures. Running `pytest` exercises all of them.

## Build matrix

| Model                       | Family     | Test file                         | What it asserts                                     |
|-----------------------------|------------|-----------------------------------|-----------------------------------------------------|
| gemini-3.7-flash-low        | Gemini 3.7 | `test_01_lowercase.py`            | All keys are lowercased before counting             |
| gemini-3.7-flash-medium     | Gemini 3.7 | `test_02_punctuation.py`          | Punctuation is stripped exactly per the contract     |
| gemini-3.7-flash-high       | Gemini 3.7 | `test_03_sorting.py`              | CLI sort order: count desc, then word asc           |
| gemini-3.6-flash-low        | Gemini 3.6 | `test_04_empty.py`                | Empty / whitespace-only input → empty dict         |
| gemini-3.6-flash-medium     | Gemini 3.6 | `test_05_unicode.py`              | Non-ASCII tokens (accents, CJK) are kept verbatim   |
| gemini-3.6-flash-high       | Gemini 3.6 | `test_06_hyphenated.py`           | Hyphenated tokens treated as single words           |
| gemini-3.5-flash-low        | Gemini 3.5 | `test_07_numbers.py`              | Tokens with digits are counted like other tokens    |
| gemini-3.5-flash-medium     | Gemini 3.5 | `test_08_repeated_input.py`       | Calling word_frequencies twice is deterministic     |
| gemini-3.5-flash-high       | Gemini 3.5 | `test_09_long_text.py`            | Handles large input without crashing               |
| gemini-3.1-pro-high         | Gemini Pro | `test_10_cli_main.py`             | CLI main() prints "word\tcount" format             |
| gemini-3.1-pro-low          | Gemini Pro | `test_11_quotes.py`               | Curly quotes are stripped like ASCII quotes        |
| claude-sonnet-4-6           | Claude     | `test_12_does_not_mutate.py`      | Returned dict is a fresh object each call          |
| claude-opus-4-6-thinking    | Claude     | `test_13_signature.py`            | Type signature is `dict[str, int]` (per __init__)   |
| gpt-oss-120b-medium         | GPT-OSS    | `test_14_idempotent_keys.py`      | Same input → same keys and same counts              |

## Run it

```bash
pip install -e .
python -m pytest -v
```

Expected: **14 test files, 14 passed**.

## How it was made

Every file in this repo was produced by a single `delegate_agy(spawn)`
call — no manual edits, no copy-paste from chat. The full transcript
lives in the commit history.

The plugin that drove the whole thing is
[`delegate_agy`](https://github.com/matheusdmlopes/hermes-delegate-agy).
