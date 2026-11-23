from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from collections.abc import Set as AbstractSet


@dataclass(frozen=True, slots=True)
class RankingEvaluationReport:
    """Metriques standard de qualite de classement Top-K."""

    k: int
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float


def precision_at_k(
    recommended_ids: Sequence[str],
    relevant_ids: AbstractSet[str],
    k: int,
) -> float:
    """Calcule la Precision@K dans [0.0, 1.0]."""
    if k < 1:
        raise ValueError("k doit etre >= 1.")
    top = list(recommended_ids[:k])
    if not top:
        return 0.0
    hits = sum(1 for item_id in top if item_id in relevant_ids)
    return round(hits / len(top), 6)


def recall_at_k(
    recommended_ids: Sequence[str],
    relevant_ids: AbstractSet[str],
    k: int,
) -> float:
    """Calcule le Recall@K dans [0.0, 1.0]."""
    if k < 1:
        raise ValueError("k doit etre >= 1.")
    if not relevant_ids:
        return 1.0
    top = set(recommended_ids[:k])
    hits = sum(1 for item_id in top if item_id in relevant_ids)
    return round(hits / len(relevant_ids), 6)


def ndcg_at_k(
    recommended_ids: Sequence[str],
    relevance_grades: Mapping[str, float],
    k: int,
) -> float:
    """Calcule le Normalized Discounted Cumulative Gain (NDCG@K) dans [0.0, 1.0]."""
    if k < 1:
        raise ValueError("k doit etre >= 1.")
    top = list(recommended_ids[:k])
    dcg = sum(
        relevance_grades.get(item_id, 0.0) / math.log2(idx + 2) for idx, item_id in enumerate(top)
    )
    ideal_grades = sorted(relevance_grades.values(), reverse=True)[:k]
    idcg = sum(grade / math.log2(idx + 2) for idx, grade in enumerate(ideal_grades))
    if idcg <= 0.0:
        return 0.0
    return round(min(1.0, dcg / idcg), 6)


def evaluate_ranking_suite(
    recommended_ids: Sequence[str],
    relevance_grades: Mapping[str, float],
    k: int,
    relevance_threshold: float = 0.5,
) -> RankingEvaluationReport:
    """Calcule simultanement Precision@K, Recall@K et NDCG@K."""
    relevant_ids = {
        item_id for item_id, grade in relevance_grades.items() if grade >= relevance_threshold
    }
    return RankingEvaluationReport(
        k=k,
        precision_at_k=precision_at_k(recommended_ids, relevant_ids, k),
        recall_at_k=recall_at_k(recommended_ids, relevant_ids, k),
        ndcg_at_k=ndcg_at_k(recommended_ids, relevance_grades, k),
    )
