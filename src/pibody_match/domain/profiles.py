from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pibody_match.domain.skills import SeniorityLevel, SkillClaim

SENSITIVE_ATTRIBUTE_BLOCKLIST: frozenset[str] = frozenset(
    {
        "gender",
        "sex",
        "sexe",
        "genre",
        "age",
        "birth_date",
        "date_naissance",
        "ethnicity",
        "ethnie",
        "race",
        "nationality",
        "nationalite",
        "religion",
        "marital_status",
        "situation_familiale",
        "disability",
        "handicap",
        "political_opinion",
        "sexual_orientation",
    }
)


@dataclass(frozen=True, slots=True)
class Profile:
    """Représentation immuable d'un talent/candidat exempte d'attributs sensibles."""

    profile_id: str
    display_name: str
    headline: str
    seniority: SeniorityLevel
    skills: tuple[SkillClaim, ...]
    objectives_text: str
    total_experience_years: float
    availability_ratio: float = 1.0
    public_tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.profile_id.strip() or not self.display_name.strip():
            raise ValueError("profile_id et display_name sont obligatoires.")
        if self.total_experience_years < 0.0:
            raise ValueError("total_experience_years ne peut pas être négative.")
        if not 0.0 <= self.availability_ratio <= 1.0:
            raise ValueError("availability_ratio doit être dans [0, 1].")
        seen_ids: set[str] = set()
        for sk in self.skills:
            if sk.skill_id in seen_ids:
                raise ValueError(f"Compétence dupliquée dans le profil : {sk.skill_id}")
            seen_ids.add(sk.skill_id)
        for tag in self.public_tags:
            norm = tag.strip().lower().split(":", 1)[0]
            if norm in SENSITIVE_ATTRIBUTE_BLOCKLIST:
                raise ValueError(f"Attribut sensible interdit dans le modèle : {tag}")

    def skill_map(self) -> dict[str, SkillClaim]:
        """Indexe les compétences détenues par skill_id."""
        return {sk.skill_id: sk for sk in self.skills}
