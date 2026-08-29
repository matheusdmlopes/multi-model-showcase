# Model: gemini-3.7-flash-low
"""Tests for validating the lowercasing contract of word_frequencies."""

from wordstats import word_frequencies


def test_single_word_mixed_case():
    """Verify that a single mixed-case word is lowercased properly."""
    assert word_frequencies("Hello") == {"hello": 1}


def test_two_words_differing_only_in_case():
    """Verify that words differing only in case are aggregated together."""
    assert word_frequencies("hello HELLO") == {"hello": 2}


def test_every_character_uppercase_input():
    """Verify that fully uppercase input is correctly lowercased and counted."""
    assert word_frequencies("HELLO WORLD") == {"hello": 1, "world": 1}


def test_case_insensitive_aggregation_across_many_repetitions():
    """Verify case-insensitive aggregation across multiple varied-case repetitions."""
    assert word_frequencies("apple Apple aPPLe") == {"apple": 3}


def test_mixed_case_with_punctuation_and_whitespace():
    """Verify that casing is normalized when tokens are mixed with punctuation and extra whitespace."""
    assert word_frequencies("  Python! pYtHoN, PYTHON...  ") == {"python": 3}


def test_mixed_case_unicode_characters():
    """Verify that unicode characters in mixed case are lowercased correctly."""
    assert word_frequencies("Café CAFÉ café") == {"café": 3}
