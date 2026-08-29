# Model: gemini-3.6-flash-low
"""Tests for validating the EMPTY-INPUT contract of word_frequencies."""

from wordstats import word_frequencies


def test_empty_string():
    """Verify that an empty string input returns an empty dictionary."""
    assert word_frequencies("") == {}


def test_single_space():
    """Verify that a single space input returns an empty dictionary."""
    assert word_frequencies(" ") == {}


def test_mixed_whitespace():
    """Verify that mixed whitespace (tab, newline, spaces) returns an empty dictionary."""
    assert word_frequencies(" \t\n \r\n\t ") == {}


def test_punctuation_only():
    """Verify that a punctuation-only string returns an empty dictionary."""
    assert word_frequencies("!?,.:;\"'()[]{}<>") == {}
