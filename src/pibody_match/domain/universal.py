from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Universe(StrEnum):
    LEARNING = "Apprentissage & Competences"
    PROJECTS = "Projets & Innovation"
    SERVICES = "Services & Expertise"
    MENTORSHIP = "Mentorat & Accompagnement"
    COMMUNITY = "Communautes & Evenements"
    OPPORTUNITIES = "Opportunites & Ressources"


class IntentType(StrEnum):
    LEARN = "apprendre"
    FIND_MENTOR = "trouver_mentor"
    BUILD_TEAM = "constituer_equipe"
    FIND_EXPERT = "trouver_expert"
    JOIN_PROJECT = "rejoindre_projet"
    JOIN_COMMUNITY = "rejoindre_communaute"


class EntityKind(StrEnum):
    PERSON = "personne"
    MENTOR = "mentor"
    PROJECT = "projet"
    RESOURCE = "formation_ressource"
    COMMUNITY = "communaute"


@dataclass(frozen=True, slots=True)
class Capability:
    skill_id: str
    canonical_name: str
    family: str
    level: float
    years: float = 1.0
    can_teach: bool = False


@dataclass(frozen=True, slots=True)
class UserEntity:
    entity_id: str
    name: str
    kind: EntityKind
    universe: Universe
    headline: str
    bio_and_goals: str
    capabilities: tuple[Capability, ...]
    experience_years: float
    availability_hours_week: int = 20
    open_to_mentor: bool = False
    open_to_collaborate: bool = True
    verified: bool = True


@dataclass(frozen=True, slots=True)
class Need:
    need_id: str
    raw_query: str
    primary_goal: str
    intent: IntentType
    universe: Universe
    target_kinds: tuple[EntityKind, ...]
    required_skills: tuple[str, ...]
    team_size: int = 1
    min_experience: float = 0.0
    requested_hours_week: int = 10
    clarification_questions: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True, slots=True)
class UniversalMatch:
    entity_id: str
    entity_name: str
    entity_kind: EntityKind
    universe: Universe
    headline: str
    compatibility_score: float
    complementarity_score: float
    reciprocity_score: float
    combined_score: float
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    is_serendipitous: bool
    discovery_reason: str
    explanation: str
    dimensions: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SkillPathStep:
    missing_skill: str
    resource_name: str
    mentor_name: str
    practice_project: str
    projected_gain: float
    rationale: str


@dataclass(frozen=True, slots=True)
class TeamComposition:
    need_id: str
    members: tuple[UniversalMatch, ...]
    collective_coverage: float
    synergy_score: float
    overall_score: float
    covered_skills: tuple[str, ...]
    uncovered_skills: tuple[str, ...]
    rationale: str
