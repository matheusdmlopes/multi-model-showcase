# Model: gemini-3.7-flash-high
"""Tests for validating sort order in wordstats.cli.main()."""

import io
from wordstats.cli import main


def test_single_word(monkeypatch, capsys):
    """Verify CLI output format and sorting for a single word."""
    monkeypatch.setattr("sys.stdin", io.StringIO("hello"))
    main()
    captured = capsys.readouterr()
    assert captured.out == "hello\t1\n"


def test_all_distinct_counts(monkeypatch, capsys):
    """Verify sorting by frequency descending when all word counts are distinct."""
    input_text = "cat dog dog bird bird bird"
    monkeypatch.setattr("sys.stdin", io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    expected = (
        "bird\t3\n"
        "dog\t2\n"
        "cat\t1\n"
    )
    assert captured.out == expected


def test_tie_breaking_alphabetical(monkeypatch, capsys):
    """Verify alphabetical tie-breaking ascending when frequencies are identical."""
    input_text = "zebra apple cherry banana date"
    monkeypatch.setattr("sys.stdin", io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    expected = (
        "apple\t1\n"
        "banana\t1\n"
        "cherry\t1\n"
        "date\t1\n"
        "zebra\t1\n"
    )
    assert captured.out == expected


def test_longer_case_multiple_ties(monkeypatch, capsys):
    """Verify sorting with multiple frequency tiers and ties within tiers."""
    # Count 3: banana, pear -> banana, pear
    # Count 2: apple, zebra -> apple, zebra
    # Count 1: date, fig, mango -> date, fig, mango
    words = [
        "pear", "banana", "banana", "pear", "banana", "pear",
        "zebra", "apple", "apple", "zebra",
        "mango", "date", "fig",
    ]
    input_text = " ".join(words)
    monkeypatch.setattr("sys.stdin", io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    expected = (
        "banana\t3\n"
        "pear\t3\n"
        "apple\t2\n"
        "zebra\t2\n"
        "date\t1\n"
        "fig\t1\n"
        "mango\t1\n"
    )
    assert captured.out == expected
