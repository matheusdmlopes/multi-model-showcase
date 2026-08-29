# Model: claude-sonnet-4-6
"""Tests that word_frequencies does not mutate the input string or shared state."""

import pytest
from wordstats import word_frequencies


def test_input_string_identity_preserved():
    """The same string object passed in should still be the same object after the call."""
    text = "hello world hello"
    original_id = id(text)
    word_frequencies(text)
    assert id(text) == original_id, "Function must not replace the caller's reference"


def test_input_string_value_unchanged():
    """The value of the input string must be identical before and after the call."""
    text = "The quick brown fox jumps over the lazy dog"
    expected = text  # capture value before call
    word_frequencies(text)
    assert text == expected, "Input string value must not change after calling word_frequencies"


def test_multiple_calls_return_independent_dicts():
    """Two calls with the same input must return distinct dict objects (not the same object)."""
    text = "apple banana apple"
    result1 = word_frequencies(text)
    result2 = word_frequencies(text)
    assert result1 is not result2, (
        "Each call must return a new dict, not the same cached object"
    )
    assert result1 == result2, "Both calls must return equal content"


def test_mutating_returned_dict_does_not_affect_future_calls():
    """Mutating the returned dict must not influence a subsequent call's result."""
    text = "cat dog cat"
    result1 = word_frequencies(text)

    # Mutate the first result aggressively
    result1["cat"] = 9999
    result1["injected"] = 42
    result1.clear()

    # A fresh call must be unaffected by mutations to the previous return value
    result2 = word_frequencies(text)
    assert result2 == {"cat": 2, "dog": 1}, (
        "Mutating a previously returned dict must not affect subsequent calls"
    )


def test_returned_dict_is_fresh_for_different_inputs():
    """Each call with a different input must also return a new dict object."""
    result_a = word_frequencies("one two three")
    result_b = word_frequencies("four five six")
    assert result_a is not result_b, (
        "Calls with different inputs must return distinct dict objects"
    )


def test_results_from_different_inputs_are_independent():
    """Mutating the result of one call must not affect the result of a call with different input."""
    text_a = "foo bar foo"
    text_b = "baz qux baz"

    result_a = word_frequencies(text_a)
    # Aggressively mutate result_a
    result_a["foo"] = 999
    result_a["injected"] = 1
    result_a.clear()

    # Result for a completely different input must be unaffected
    result_b = word_frequencies(text_b)
    assert result_b == {"baz": 2, "qux": 1}, (
        "Mutating one call's result must not affect results from calls with different input"
    )
