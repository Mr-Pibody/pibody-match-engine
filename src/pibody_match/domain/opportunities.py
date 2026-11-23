from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pibody_match.domain.skills import SeniorityLevel, SkillRequirement


@dataclass(frozen=True, slots=True)
class Opportunity:
    """Opportunité, mission ou projet à pourvoir."""

    opportunity_id: str
    title: str
    organization: str
    description_text: str
    objectives_text: str
    requirements: tuple[SkillRequirement, ...]
    min_total_experience: float = 0.0
    preferred_seniority: SeniorityLevel | None = None
    capacity: int = 1
    domain_tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.opportunity_id.strip() or not self.title.strip():
            raise ValueError("opportunity_id et title sont obligatoires.")
        if not self.requirements:
            raise ValueError("Une opportunité doit définir au moins une exigence.")
        if self.min_total_experience < 0.0:
            raise ValueError("min_total_experience ne peut pas être négative.")
        if self.capacity < 1:
            raise ValueError("capacity doit être >= 1.")
        seen: set[str] = set()
        for req in self.requirements:
            if req.skill_id in seen:
                raise ValueError(f"Exigence dupliquée : {req.skill_id}")
            seen.add(req.skill_id)
