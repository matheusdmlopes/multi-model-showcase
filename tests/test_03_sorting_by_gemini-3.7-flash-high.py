# Model: gemini-3.7-flash-high
"""Tests for the CLI ordering contract."""

import io

from wordstats.cli import main


def run_cli(monkeypatch, capsys, text):
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    main()
    return capsys.readouterr().out


def test_single_word(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "hello") == "hello\t1\n"


def test_descending_count(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "cat dog dog bird bird bird") == "bird\t3\ndog\t2\ncat\t1\n"


def test_alphabetical_tie_breaking(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "zebra apple cherry") == "apple\t1\ncherry\t1\nzebra\t1\n"


def test_multiple_count_tiers(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "pear banana banana pear banana pear zebra apple apple zebra") == "banana\t3\npear\t3\napple\t2\nzebra\t2\n"


def test_prefix_tie_breaking(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "app apple application app apple application application") == "application\t3\napp\t2\napple\t2\n"


def test_normalized_sorting(monkeypatch, capsys):
    assert run_cli(monkeypatch, capsys, "Zebra! apple, APPLE... zebra \"banana\"") == "apple\t2\nzebra\t2\nbanana\t1\n"
