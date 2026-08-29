# Model: gemini-3.6-flash-medium
"""Tests for validating Unicode non-ASCII token preservation contract in word_frequencies."""

from wordstats import word_frequencies


def test_accented_latin_lowercased():
    """Verify that accented Latin characters (e.g., café, naïve, München) are lowercased and retained."""
    result = word_frequencies("CAFÉ Café café NAÏVE Naïve MÜNCHEN münchen")
    assert result == {"café": 3, "naïve": 2, "münchen": 2}


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


def test_cyrillic_and_greek_script_lowercasing():
    """Verify that non-Latin cased scripts like Cyrillic and Greek are correctly lowercased and aggregated."""
    result = word_frequencies("ПРИВЕТ привет ΓΕΙΆ γειά")
    assert result == {"привет": 2, "γειά": 2}


def test_unicode_curly_quotes_stripped_around_non_ascii():
    """Verify that unicode curly quotes (‘ ’ “ ”) in PUNCTUATION are stripped from non-ASCII words."""
    result = word_frequencies("“café” ‘naïve’ «über»")
    assert result == {"café": 1, "naïve": 1, "«über»": 1}


def test_unicode_punctuation_em_dash_and_inverted_marks_retained():
    """Verify that Unicode punctuation not in PUNCTUATION (e.g. em-dash '—', '¿', '¡') is retained."""
    result = word_frequencies("¿word—another? ¡—test—!")
    assert result == {"¿word—another": 1, "¡—test—": 1}


def test_emoji_and_symbol_tokens_preserved():
    """Verify that non-ASCII emoji and symbol tokens are preserved without error."""
    result = word_frequencies("🚀 python 🚀 code 🐍")
    assert result == {"🚀": 2, "python": 1, "code": 1, "🐍": 1}


def test_unicode_whitespace_splitting():
    """Verify that Unicode whitespace characters (non-breaking space, ideographic space) split tokens."""
    result = word_frequencies("café\u00a0naïve\u3000münchen")
    assert result == {"café": 1, "naïve": 1, "münchen": 1}
