# Model: gemini-3.5-flash-low
"""Tests for validating digit token handling in word_frequencies."""

from wordstats import word_frequencies


def test_single_token_with_digits():
    """Verify that a single token containing digits is processed as a single key."""
    assert word_frequencies("abc123") == {"abc123": 1}
    assert word_frequencies("2024") == {"2024": 1}
    assert word_frequencies("iso9001") == {"iso9001": 1}


def test_two_different_digit_tokens():
    """Verify that two different tokens containing digits are counted separately."""
    result = word_frequencies("abc123 iso9001")
    assert result == {"abc123": 1, "iso9001": 1}


def test_digit_token_repeated():
    """Verify that a token containing digits repeated is counted correctly."""
    result = word_frequencies("2024 2024 2024")
    assert result == {"2024": 3}


def test_mixed_digits_and_letters_in_sentence():
    """Verify mixed digits and letters in a sentence are processed correctly, preserving digits."""
    text = "The year 2024 is under the ISO9001 standard for abc123 code."
    expected = {
        "the": 2,
        "year": 1,
        "2024": 1,
        "is": 1,
        "under": 1,
        "iso9001": 1,
        "standard": 1,
        "for": 1,
        "abc123": 1,
        "code": 1
    }
    assert word_frequencies(text) == expected
