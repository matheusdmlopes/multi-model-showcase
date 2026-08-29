# Model: gemini-3.1-pro-high
import sys
import io
from wordstats.cli import main

def test_cli_format_typical_input(monkeypatch, capsys):
    input_text = "hello world hello"
    monkeypatch.setattr('sys.stdin', io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    assert captured.out == "hello\t2\nworld\t1\n"

def test_cli_format_empty_input(monkeypatch, capsys):
    input_text = ""
    monkeypatch.setattr('sys.stdin', io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    assert captured.out == ""

def test_cli_format_single_word(monkeypatch, capsys):
    input_text = "test"
    monkeypatch.setattr('sys.stdin', io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    assert captured.out == "test\t1\n"

def test_cli_format_multi_word_unique(monkeypatch, capsys):
    input_text = "one two three"
    monkeypatch.setattr('sys.stdin', io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    assert captured.out == "one\t1\nthree\t1\ntwo\t1\n"
