# Model: gemini-3.5-flash-high
"""Tests for large-input behavior in word_frequencies."""

from wordstats import word_frequencies


def test_one_thousand_unique_tokens():
    text = " ".join(f"word{index}" for index in range(1000))
    result = word_frequencies(text)
    assert len(result) == 1000
    assert result["word999"] == 1


def test_ten_thousand_unique_tokens():
    text = " ".join(f"token{index}" for index in range(10000))
    result = word_frequencies(text)
    assert len(result) == 10000
    assert result["token9999"] == 1


def test_repeated_token_at_scale():
    result = word_frequencies(" ".join(["hello"] * 5000))
    assert result == {"hello": 5000}


def test_large_mixed_input_counts_clean_tokens():
    text = " ".join(["apple"] * 2000 + ["banana!"] * 2000 + ["!!!"] * 1000)
    assert word_frequencies(text) == {"apple": 2000, "banana": 2000}


def test_large_punctuation_only_input_is_empty():
    text = " ".join(["!!!", "???", "...", "::;"] * 4000)
    assert word_frequencies(text) == {}


def test_large_mixed_whitespace_input():
    tokens = ["word", "another", "token", "count"] * 5000
    whitespace = [" ", "\t", "\n", "\r\n"]
    text = "".join(token + whitespace[index % len(whitespace)] for index, token in enumerate(tokens))
    assert word_frequencies(text) == {"word": 5000, "another": 5000, "token": 5000, "count": 5000}


def test_large_cardinality_and_repetition():
    text = " ".join([f"u{index}" for index in range(50000)] + ["common"] * 50000)
    result = word_frequencies(text)
    assert len(result) == 50001
    assert result["common"] == 50000


def test_extreme_token_length_is_preserved_after_cleaning():
    token = "!" + "a" * 998 + "?"
    result = word_frequencies(" ".join([token] * 1000))
    assert result == {"a" * 998: 1000}
