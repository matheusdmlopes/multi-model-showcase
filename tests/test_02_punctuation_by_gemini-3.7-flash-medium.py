# Model: gemini-3.7-flash-medium
"""Tests for validating the punctuation stripping contract of word_frequencies."""

import pytest
from wordstats import PUNCTUATION, word_frequencies


def test_individual_punctuation_categories():
    """Verify stripping of individual punctuation categories: sentence marks, brackets, and quotes."""
    # Sentence punctuation
    assert word_frequencies("hello. world, test; item: stop! really?") == {
        "hello": 1,
        "world": 1,
        "test": 1,
        "item": 1,
        "stop": 1,
        "really": 1,
    }

    # Brackets and enclosures: (), [], {}, <>
    assert word_frequencies("(parentheses) [brackets] {braces} <angles>") == {
        "parentheses": 1,
        "brackets": 1,
        "braces": 1,
        "angles": 1,
    }

    # Straight and curly quotes: ", ', “, ”, ‘, ’
    assert word_frequencies('"double" \'single\' “curly_double” ‘curly_single’') == {
        "double": 1,
        "single": 1,
        "curly_double": 1,
        "curly_single": 1,
    }


def test_all_defined_punctuation_characters_stripped():
    """Verify that every single character in PUNCTUATION constant is stripped from token boundaries."""
    for char in PUNCTUATION:
        wrapped = f"{char}token{char}"
        assert word_frequencies(wrapped) == {"token": 1}, f"Failed to strip {char!r} from token"
        assert word_frequencies(char) == {}, f"Failed to treat standalone punctuation {char!r} as empty"


def test_punctuation_position_start_end_both():
    """Verify punctuation stripping at start only, end only, and both start and end."""
    # Punctuation at start only
    assert word_frequencies("!start (open <lead") == {
        "start": 1,
        "open": 1,
        "lead": 1,
    }

    # Punctuation at end only
    assert word_frequencies("finish! close) trail>") == {
        "finish": 1,
        "close": 1,
        "trail": 1,
    }

    # Punctuation at both start and end
    assert word_frequencies('"both" [surrounded] “wrapped”') == {
        "both": 1,
        "surrounded": 1,
        "wrapped": 1,
    }


def test_all_punctuation_edge_case():
    """Verify that inputs consisting entirely of punctuation return an empty dictionary."""
    assert word_frequencies("...") == {}
    assert word_frequencies("!?!?") == {}
    assert word_frequencies(".,;:!?\"'()[]{}<>“”‘’") == {}
    assert word_frequencies("  ...   ???   !!!   ") == {}
    assert word_frequencies("() [] {} <> \"\" '' “” ‘’") == {}
    assert word_frequencies(PUNCTUATION) == {}


def test_stacked_and_consecutive_punctuation_stripping():
    """Verify stripping of multiple consecutive and stacked punctuation marks."""
    assert word_frequencies("...hello... (((world))) !?!?[nested]!?!?") == {
        "hello": 1,
        "world": 1,
        "nested": 1,
    }
    assert word_frequencies("“‘double-nested’”") == {"double-nested": 1}
    assert word_frequencies("<{[((complex-enclosure))]}>") == {"complex-enclosure": 1}


def test_internal_punctuation_preserved_while_boundary_stripped():
    """Verify that leading and trailing punctuation is stripped while internal punctuation is retained."""
    assert word_frequencies('("don\'t")') == {"don't": 1}
    assert word_frequencies('"U.S.A."') == {"u.s.a": 1}
    assert word_frequencies("...state-of-the-art...") == {"state-of-the-art": 1}
    assert word_frequencies("{key:value}") == {"key:value": 1}


def test_isolated_punctuation_tokens_among_words():
    """Verify standalone punctuation tokens interspersed with words are ignored."""
    assert word_frequencies("hello ... world ??? : python !") == {
        "hello": 1,
        "world": 1,
        "python": 1,
    }


def test_mixed_sentence_with_punctuation_and_aggregation():
    """Verify correct aggregation and stripping in realistic sentences with varied punctuation."""
    text = '“Hello, World!” said Alice (or was it "Alice"?). Alice, hello!'
    expected = {
        "hello": 2,
        "world": 1,
        "said": 1,
        "alice": 3,
        "or": 1,
        "was": 1,
        "it": 1,
    }
    assert word_frequencies(text) == expected
