# Model: gpt-oss-120b-medium
"""Tests for idempotency of `word_frequencies`.

The tests verify that repeated calls with the same input produce identical
outputs, that the union of keys from separate calls matches a single call on
the concatenated input (ignoring whitespace), and that the function does not
retain any state between invocations.
"""

import pytest
from src.wordstats import word_frequencies


def normalize_counts(d: dict[str, int]) -> dict[str, int]:
    """Return a copy with keys sorted for deterministic comparison.
    The function itself is deterministic, so this helper is just for clarity.
    """
    return dict(sorted(d.items()))


def test_same_input_twice_produces_identical_output():
    text = "Hello world! Hello, world."
    result1 = normalize_counts(word_frequencies(text))
    result2 = normalize_counts(word_frequencies(text))
    assert result1 == result2
    # Ensure keys and counts are as expected
    assert result1 == {"hello": 2, "world": 2}


def test_three_calls_same_input_all_equal():
    text = "foo bar baz foo"
    results = [normalize_counts(word_frequencies(text)) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert results[0] == {"foo": 2, "bar": 1, "baz": 1}


def test_disjoint_inputs_union_equals_concatenated():
    text1 = "apple banana"
    text2 = "carrot apple"
    # Separate calls
    counts1 = normalize_counts(word_frequencies(text1))
    counts2 = normalize_counts(word_frequencies(text2))
    # Union of keys and summed counts
    combined = {}
    for d in (counts1, counts2):
        for k, v in d.items():
            combined[k] = combined.get(k, 0) + v
    # Single call on concatenated input (with whitespace)
    concatenated = f"{text1} {text2}"
    counts_concat = normalize_counts(word_frequencies(concatenated))
    assert combined == counts_concat


def test_no_state_accumulation_between_calls():
    # First call with a key
    word_frequencies("unique1")
    # Second call with a different key; result should not include previous key
    result = normalize_counts(word_frequencies("unique2"))
    assert result == {"unique2": 1}
    # Ensure calling again with original key gives correct count
    assert normalize_counts(word_frequencies("unique1")) == {"unique1": 1}
