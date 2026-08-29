"""CLI module for wordstats."""

import sys
from wordstats import word_frequencies


def main() -> None:
    """Read from stdin, compute word frequencies, and print results."""
    text = sys.stdin.read()
    frequencies = word_frequencies(text)
    sorted_items = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
    for word, count in sorted_items:
        print(f"{word}\t{count}")


if __name__ == "__main__":
    main()
