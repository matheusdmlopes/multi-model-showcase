# Model: gemini-3.5-flash-high
"""Tests for validating scalability of word_frequencies on large input."""

from wordstats import word_frequencies


def test_scalability_1000_tokens():
    """Test word_frequencies with 1000 unique tokens."""
    words = [f"word{i}" for i in range(1000)]
    text = " ".join(words)
    res = word_frequencies(text)
    assert len(res) == 1000
    for i in range(1000):
        assert res[f"word{i}"] == 1


def test_scalability_10000_tokens():
    """Test word_frequencies with 10000 unique tokens."""
    words = [f"token{i}" for i in range(10000)]
    text = " ".join(words)
    res = word_frequencies(text)
    assert len(res) == 10000
    for i in range(10000):
        assert res[f"token{i}"] == 1


def test_scalability_single_word_repeated_5000():
    """Test word_frequencies with a single word repeated 5000 times."""
    word = "hello"
    text = " ".join([word] * 5000)
    res = word_frequencies(text)
    assert len(res) == 1
    assert res[word] == 5000


def test_scalability_large_deterministic_input():
    """Test word_frequencies with a large deterministic input and verify sum-of-counts matches non-empty tokens."""
    words = (["apple"] * 2000) + (["banana!"] * 2000) + (["!!!"] * 1000)
    text = " ".join(words)
    res = word_frequencies(text)
    
    assert res["apple"] == 2000
    assert res["banana"] == 2000
    assert "banana!" not in res
    assert "" not in res
    
    # Calculate sum of counts
    total_counts_sum = sum(res.values())
    
    # Calculate non-empty token count based on package cleaning rules
    punctuation = '.,;:!?"\'()[]{}<>“”‘’'
    non_empty_count = sum(1 for token in text.split() if token.lower().strip(punctuation))
    
    assert non_empty_count == 4000
    assert total_counts_sum == non_empty_count
