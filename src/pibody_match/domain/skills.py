from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SeniorityLevel(StrEnum):
    """Niveau de séniorité normalisé d'un profil."""

    JUNIOR = "Junior"
    CONFIRME = "Confirmé"
    SENIOR = "Senior"
    EXPERT = "Expert"


class GapStatus(StrEnum):
    """Statut de couverture d'une compétence exigée."""

    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


@dataclass(frozen=True, slots=True)
class SkillClaim:
    """Compétence détenue par un profil avec niveau, expérience et vérification."""

    skill_id: str
    raw_name: str
    canonical_name: str
    family: str
    proficiency: float
    years_experience: float = 0.0
    verified: bool = False

    def __post_init__(self) -> None:
        if not self.skill_id.strip() or not self.canonical_name.strip():
            raise ValueError("skill_id et canonical_name sont obligatoires.")
        if not 0.0 <= self.proficiency <= 1.0:
            raise ValueError(f"proficiency hors bornes [0, 1] : {self.proficiency}")
        if self.years_experience < 0.0:
            raise ValueError(f"years_experience négative interdite : {self.years_experience}")


@dataclass(frozen=True, slots=True)
class SkillRequirement:
    """Exigence de compétence portée par une opportunité."""

    skill_id: str
    canonical_name: str
    family: str
    min_proficiency: float
    min_years: float = 0.0
    weight: float = 1.0
    mandatory: bool = False

    def __post_init__(self) -> None:
        if not self.skill_id.strip() or not self.canonical_name.strip():
            raise ValueError("skill_id et canonical_name sont obligatoires.")
        if not 0.0 <= self.min_proficiency <= 1.0:
            raise ValueError(f"min_proficiency hors bornes [0, 1] : {self.min_proficiency}")
        if self.min_years < 0.0:
            raise ValueError(f"min_years négative interdite : {self.min_years}")
        if self.weight <= 0.0:
            raise ValueError(f"weight doit être strictement positif : {self.weight}")


@dataclass(frozen=True, slots=True)
class SkillGapItem:
    """Diagnostic détaillé de l'écart entre une exigence et un profil."""

    skill_id: str
    canonical_name: str
    family: str
    status: GapStatus
    mandatory: bool
    required_proficiency: float
    actual_proficiency: float
    effective_proficiency: float
    coverage_ratio: float
    matched_via: str | None = None
    taxonomic_similarity: float = 0.0
