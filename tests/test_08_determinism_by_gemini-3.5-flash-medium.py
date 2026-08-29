# Model: gemini-3.5-flash-medium
"""Tests for validating determinism of word_frequencies."""

import concurrent.futures
from wordstats import word_frequencies


def test_same_input_twice_equal():
    """Verify that calling word_frequencies twice with the same input returns equal dictionaries."""
    text = "hello world hello"
    res1 = word_frequencies(text)
    res2 = word_frequencies(text)
    assert res1 == res2
    assert res1 is not res2
    assert list(res1.keys()) == list(res2.keys())


def test_calling_five_times_all_equal():
    """Verify that calling word_frequencies 5 times in a row with the same input returns equal dictionaries."""
    text = "pytest testing pytest determinism test"
    results = [word_frequencies(text) for _ in range(5)]
    first = results[0]
    for r in results[1:]:
        assert r == first
        assert list(r.keys()) == list(first.keys())
        assert r is not first


def test_two_different_inputs_independent():
    """Verify that two different inputs produce two independent and correct dictionaries, without cross-call state."""
    text1 = "apple orange banana"
    text2 = "grape melon"
    res1 = word_frequencies(text1)
    res2 = word_frequencies(text2)
    assert res1 == {"apple": 1, "orange": 1, "banana": 1}
    assert res2 == {"grape": 1, "melon": 1}


def test_mutation_does_not_affect_subsequent_call():
    """Verify that mutating a returned dictionary does not affect subsequent calls to word_frequencies."""
    text = "check reference safety"
    res1 = word_frequencies(text)

    # Mutate the dictionary
    res1["check"] = 999
    res1["new_key"] = 123

    res2 = word_frequencies(text)
    assert res2 == {"check": 1, "reference": 1, "safety": 1}
    assert "new_key" not in res2


def test_empty_and_punctuation_mutation_safety():
    """Verify that mutating dictionaries returned by empty or punctuation-only inputs does not affect subsequent calls."""
    # Test empty string
    res_empty1 = word_frequencies("")
    assert res_empty1 == {}
    res_empty1["corrupt"] = 99

    res_empty2 = word_frequencies("")
    assert res_empty2 == {}
    assert "corrupt" not in res_empty2

    # Test punctuation only
    res_punc1 = word_frequencies("!!!  ???")
    assert res_punc1 == {}
    res_punc1["corrupt"] = 99

    res_punc2 = word_frequencies("!!!  ???")
    assert res_punc2 == {}
    assert "corrupt" not in res_punc2


def test_concurrent_calls_determinism():
    """Verify that calling word_frequencies concurrently from multiple threads yields deterministic results."""
    text = "concurrency thread safety and determinism validation test"
    expected = word_frequencies(text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(word_frequencies, text) for _ in range(30)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for r in results:
        assert r == expected
        assert list(r.keys()) == list(expected.keys())
        assert r is not expected
