# Model: gemini-3.1-pro-low
import pytest
from wordstats import word_frequencies

def test_curly_double_quotes():
    assert word_frequencies("“hello”") == {"hello": 1}

def test_curly_single_quotes():
    assert word_frequencies("‘world’") == {"world": 1}

def test_mixed_straight_curly():
    assert word_frequencies("\"test” ‘case'") == {"test": 1, "case": 1}

def test_curly_adjacent_to_punctuation():
    assert word_frequencies("“wow!?”") == {"wow": 1}

def test_inner_curly_quotes_preserved():
    assert word_frequencies("don’t won’t") == {"don’t": 1, "won’t": 1}

def test_multiple_layered_curly_quotes():
    assert word_frequencies("“‘hello’”") == {"hello": 1}
