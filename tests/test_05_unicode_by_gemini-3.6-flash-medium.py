# Model: gemini-3.6-flash-medium
"""Tests for validating Unicode handling contract in word_frequencies."""

from wordstats import word_frequencies


def test_accented_latin_lowercased():
    """Verify that accented Latin characters (e.g., café, naïve) are lowercased and retained."""
    result = word_frequencies("CAFÉ Café café NAÏVE Naïve")
    assert result == {"café": 3, "naïve": 2}


def test_cjk_preserved():
    """Verify that CJK characters (e.g., nihongo / 日本語) are preserved and counted."""
    result = word_frequencies("日本語 日本語 中文")
    assert result == {"日本語": 2, "中文": 1}


def test_mixed_ascii_unicode():
    """Verify that text containing a mix of ASCII and Unicode words processes correctly."""
    result = word_frequencies("Hello, 世界! Welcome to the café.")
    assert result == {
        "hello": 1,
        "世界": 1,
        "welcome": 1,
        "to": 1,
        "the": 1,
        "café": 1,
    }


def test_unicode_punctuation_em_dash_not_stripped():
    """Verify that Unicode punctuation not in PUNCTUATION (like em-dash '—') is NOT stripped."""
    result = word_frequencies("word—another —test—")
    assert result == {"word—another": 1, "—test—": 1}
