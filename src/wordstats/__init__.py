"""wordstats - A minimal word frequency statistics package."""

__all__ = ["word_frequencies"]

PUNCTUATION = '.,;:!?"\'()[]{}<>“”‘’'


def word_frequencies(text: str) -> dict[str, int]:
    """Calculate word frequencies from text.

    Splits input on whitespace, converts tokens to lowercase,
    strips punctuation characters, and returns a dictionary of word counts.
    Empty input returns an empty dictionary.
    """
    if not text:
        return {}

    counts: dict[str, int] = {}
    for token in text.split():
        cleaned = token.lower().strip(PUNCTUATION)
        if cleaned:
            counts[cleaned] = counts.get(cleaned, 0) + 1
    return counts
