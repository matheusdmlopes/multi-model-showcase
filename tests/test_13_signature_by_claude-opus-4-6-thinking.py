# Model: claude-opus-4-6-thinking
"""Tests validating the type signature and module exports of word_frequencies."""

import inspect

import wordstats
from wordstats import word_frequencies


def test_word_frequencies_is_callable():
    """word_frequencies must be a callable function."""
    assert callable(word_frequencies)


def test_word_frequencies_returns_dict():
    """word_frequencies must return a dict."""
    result = word_frequencies("hello world")
    assert isinstance(result, dict)


def test_word_frequencies_values_are_all_int():
    """Every value in the returned dict must be an int."""
    result = word_frequencies("one two two three three three")
    assert result  # non-empty so the check is meaningful
    for key, value in result.items():
        assert isinstance(value, int), f"Value for key {key!r} is {type(value).__name__}, expected int"


def test_word_frequencies_exported_in_all():
    """word_frequencies must appear in wordstats.__all__."""
    assert hasattr(wordstats, "__all__"), "wordstats module has no __all__"
    assert "word_frequencies" in wordstats.__all__


def test_word_frequencies_has_expected_signature():
    """word_frequencies must accept a single parameter 'text' annotated as str."""
    sig = inspect.signature(word_frequencies)
    params = list(sig.parameters.values())
    assert len(params) == 1, f"Expected 1 parameter, got {len(params)}"
    param = params[0]
    assert param.name == "text"
    assert param.annotation is str, f"Expected annotation str, got {param.annotation}"
