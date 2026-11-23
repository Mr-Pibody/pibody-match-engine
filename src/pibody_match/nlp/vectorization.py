from __future__ import annotations

import math
from collections import Counter
from typing import TYPE_CHECKING

from pibody_match.nlp.normalization import tokenize

if TYPE_CHECKING:
    from collections.abc import Sequence


class TfidfVectorizer:
    """Vectoriseur TF-IDF deterministe avec normalisation euclidienne L2."""

    def __init__(self) -> None:
        self._idf: dict[str, float] = {}
        self._fitted: bool = False

    @property
    def vocabulary_size(self) -> int:
        """Nombre de termes indexes dans le vocabulaire."""
        return len(self._idf)

    def fit(self, documents: Sequence[str]) -> TfidfVectorizer:
        """Calcule les poids IDF lisses sur un corpus de documents."""
        doc_count = len(documents)
        df_counts: Counter[str] = Counter()
        for doc in documents:
            df_counts.update(set(tokenize(doc)))

        self._idf = {
            term: math.log((doc_count + 1.0) / (df + 1.0)) + 1.0
            for term, df in sorted(df_counts.items())
        }
        self._fitted = True
        return self

    def transform(self, text: str) -> dict[str, float]:
        """Transforme un texte en vecteur creux TF-IDF normalise L2."""
        if not self._fitted:
            raise RuntimeError("TfidfVectorizer doit etre entraine via fit() avant transform().")
        tokens = tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        total_tokens = float(len(tokens))
        raw_weights: dict[str, float] = {}
        for term, count in counts.items():
            idf = self._idf.get(term)
            if idf is not None:
                raw_weights[term] = (count / total_tokens) * idf

        norm = math.sqrt(sum(val * val for val in raw_weights.values()))
        if norm == 0.0:
            return {}
        return {term: val / norm for term, val in raw_weights.items()}

    def fit_transform(self, documents: Sequence[str]) -> list[dict[str, float]]:
        """Entraine le vectoriseur puis transforme chaque document."""
        self.fit(documents)
        return [self.transform(doc) for doc in documents]
