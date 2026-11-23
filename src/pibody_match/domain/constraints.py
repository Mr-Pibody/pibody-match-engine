from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HumanDecision(StrEnum):
    """Décision humaine explicite sur une recommandation (Human-in-the-loop)."""

    PENDING = "PENDING"
    SHORTLISTED = "SHORTLISTED"
    IN_REVIEW = "IN_REVIEW"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class MatchConstraints:
    """Contraintes de filtrage et seuils d'acceptation configurables."""

    min_score: float = 0.0
    strict_mandatory: bool = False
    min_availability: float = 0.0
    confidence_threshold: float = 0.70

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score doit être dans [0, 1].")
        if not 0.0 <= self.min_availability <= 1.0:
            raise ValueError("min_availability doit être dans [0, 1].")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold doit être dans [0, 1].")
