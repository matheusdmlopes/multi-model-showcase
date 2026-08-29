# Model: gemini-3.6-flash-high
"""Tests for validating hyphenated token handling in word_frequencies."""

from wordstats import word_frequencies


def test_simple_hyphenated_word_kept_as_one_key():
    """Verify that a simple hyphenated word is preserved as a single key with hyphen retained."""
    result = word_frequencies("well-known well-known")
    assert result == {"well-known": 2}


def test_two_different_hyphenated_words_counted_separately():
    """Verify that two distinct hyphenated words are tracked and counted as separate keys."""
    result = word_frequencies("well-known state-of-the-art well-known")
    assert result == {"well-known": 2, "state-of-the-art": 1}


def test_hyphenated_word_next_to_regular_word():
    """Verify that hyphenated words coexist correctly with regular non-hyphenated words."""
    result = word_frequencies("A well-known fact is a fact")
    assert result == {"a": 2, "well-known": 1, "fact": 2, "is": 1}


def test_hyphenated_word_with_surrounding_punctuation():
    """Verify that surrounding punctuation is stripped while preserving internal hyphens."""
    result = word_frequencies(", well-known,")
    assert result == {"well-known": 1}
