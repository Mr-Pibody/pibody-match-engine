from __future__ import annotations

import re
import unicodedata

STOPWORDS_FR_EN: frozenset[str] = frozenset(
    {
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "du",
        "de",
        "d",
        "et",
        "ou",
        "en",
        "dans",
        "sur",
        "pour",
        "par",
        "avec",
        "sans",
        "au",
        "aux",
        "ce",
        "ces",
        "se",
        "sa",
        "son",
        "ses",
        "nos",
        "vos",
        "leur",
        "leurs",
        "qui",
        "que",
        "quoi",
        "dont",
        "est",
        "sont",
        "etre",
        "avoir",
        "plus",
        "tres",
        "the",
        "a",
        "an",
        "and",
        "or",
        "in",
        "on",
        "for",
        "to",
        "of",
        "with",
        "by",
        "is",
        "are",
        "be",
        "as",
        "at",
        "from",
        "that",
        "this",
        "it",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[+#.][a-z0-9+#]*)*")


def tokenize(text: str) -> list[str]:
    """Normalise un texte FR/EN et extrait les jetons techniques pertinents."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    raw_tokens = _TOKEN_RE.findall(stripped)
    return [
        tok
        for tok in raw_tokens
        if tok not in STOPWORDS_FR_EN and (len(tok) > 1 or tok in {"c", "r"})
    ]
