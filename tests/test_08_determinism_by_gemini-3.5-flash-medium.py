# Model: gemini-3.5-flash-medium
"""Tests for validating determinism of word_frequencies."""

from wordstats import word_frequencies


def test_same_input_twice_equal():
    """Verify that calling word_frequencies twice with the same input returns equal dictionaries."""
    text = "hello world hello"
    res1 = word_frequencies(text)
    res2 = word_frequencies(text)
    assert res1 == res2
    assert res1 is not res2


def test_calling_five_times_all_equal():
    """Verify that calling word_frequencies 5 times in a row with the same input returns equal dictionaries."""
    text = "pytest testing pytest determinism test"
    results = [word_frequencies(text) for _ in range(5)]
    first = results[0]
    for r in results[1:]:
        assert r == first


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
