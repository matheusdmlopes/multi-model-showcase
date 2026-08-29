# Model: gemini-3.1-pro-high
import io
import pytest
from wordstats.cli import main

@pytest.mark.parametrize(
    "input_text, expected_out",
    [
        ("hello world hello", "hello\t2\nworld\t1\n"),
        ("", ""),
        ("test", "test\t1\n"),
        ("one two three", "one\t1\nthree\t1\ntwo\t1\n"),
        ("a b c a c c", "c\t3\na\t2\nb\t1\n"),
    ]
)
def test_cli_format(monkeypatch, capsys, input_text, expected_out):
    monkeypatch.setattr("sys.stdin", io.StringIO(input_text))
    main()
    captured = capsys.readouterr()
    assert captured.out == expected_out
    assert captured.err == ""
