from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def cosine_similarity(vec_a: Mapping[str, float], vec_b: Mapping[str, float]) -> float:
    """Calcule la similarite cosinus symetrique dans [0.0, 1.0] entre deux vecteurs L2."""
    if not vec_a or not vec_b:
        return 0.0
    smaller, larger = (vec_a, vec_b) if len(vec_a) <= len(vec_b) else (vec_b, vec_a)
    dot = sum(val * larger.get(term, 0.0) for term, val in smaller.items())
    return min(1.0, max(0.0, dot))


def explain_lexical_overlap(
    vec_a: Mapping[str, float],
    vec_b: Mapping[str, float],
    top_n: int = 5,
) -> list[tuple[str, float]]:
    """Retourne les termes communs les plus contributifs entre deux vecteurs."""
    shared = [(term, round(val * vec_b[term], 4)) for term, val in vec_a.items() if term in vec_b]
    shared.sort(key=lambda item: (-item[1], item[0]))
    return shared[:top_n]
