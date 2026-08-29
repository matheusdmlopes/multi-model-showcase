# Model: gemini-3.5-flash-low
"""Tests for digit-containing token handling in word_frequencies."""

from wordstats import word_frequencies


def test_alphanumeric_token_is_a_key():
    assert word_frequencies("abc123") == {"abc123": 1}


def test_numeric_token_is_a_key():
    assert word_frequencies("2024") == {"2024": 1}


def test_distinct_digit_tokens_are_separate():
    assert word_frequencies("abc123 iso9001") == {"abc123": 1, "iso9001": 1}


def test_repeated_digit_token_is_counted():
    assert word_frequencies("2024 2024 2024") == {"2024": 3}


def test_boundary_punctuation_is_stripped():
    assert word_frequencies("iso9001! [abc123] 2024, (2024).") == {
        "iso9001": 1,
        "abc123": 1,
        "2024": 2,
    }


def test_digit_tokens_are_case_insensitive():
    assert word_frequencies("Abc123 aBc123 ABC123") == {"abc123": 3}
