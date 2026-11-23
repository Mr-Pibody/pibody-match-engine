from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pibody_match.domain.constraints import MatchConstraints
from pibody_match.explanations.match_explanation import MatchExplanation, build_match_explanation
from pibody_match.nlp.vectorization import TfidfVectorizer
from pibody_match.scoring.compatibility import ScoreBreakdown, compute_compatibility
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pibody_match.domain.opportunities import Opportunity
    from pibody_match.domain.profiles import Profile
    from pibody_match.domain.skills import SkillGapItem


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Resultat complet et tracable d'un appariement candidat-opportunite."""

    match_id: str
    profile_id: str
    profile_name: str
    opportunity_id: str
    opportunity_title: str
    breakdown: ScoreBreakdown
    skill_gaps: tuple[SkillGapItem, ...]
    explanation: MatchExplanation
    meets_constraints: bool


def _build_corpus_vectorizer(
    profiles: Sequence[Profile],
    opportunities: Sequence[Opportunity],
) -> TfidfVectorizer:
    docs = [f"{p.headline} {p.objectives_text}" for p in profiles] + [
        f"{o.title} {o.description_text} {o.objectives_text}" for o in opportunities
    ]
    return TfidfVectorizer().fit(docs)


def evaluate_match(
    profile: Profile,
    opportunity: Opportunity,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    constraints: MatchConstraints | None = None,
    taxonomy: SkillTaxonomyGraph | None = None,
    vectorizer: TfidfVectorizer | None = None,
) -> MatchResult:
    """Evalue une paire (profil, opportunite) et verifie les contraintes."""
    active_constraints = constraints if constraints is not None else MatchConstraints()
    breakdown, gaps, overlap = compute_compatibility(
        profile=profile,
        opportunity=opportunity,
        weights=weights,
        taxonomy=taxonomy,
        vectorizer=vectorizer,
    )
    explanation = build_match_explanation(profile, opportunity, breakdown, gaps, overlap)

    meets = (
        breakdown.total_score >= active_constraints.min_score
        and profile.availability_ratio >= active_constraints.min_availability
        and (
            not active_constraints.strict_mandatory or len(breakdown.missing_mandatory_skills) == 0
        )
    )
    return MatchResult(
        match_id=f"match_{profile.profile_id}_{opportunity.opportunity_id}",
        profile_id=profile.profile_id,
        profile_name=profile.display_name,
        opportunity_id=opportunity.opportunity_id,
        opportunity_title=opportunity.title,
        breakdown=breakdown,
        skill_gaps=gaps,
        explanation=explanation,
        meets_constraints=meets,
    )


def rank_opportunities_for_profile(
    profile: Profile,
    opportunities: Sequence[Opportunity],
    top_k: int = 5,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    constraints: MatchConstraints | None = None,
    taxonomy: SkillTaxonomyGraph | None = None,
) -> list[MatchResult]:
    """Classe de maniere deterministe les Top-K opportunites pour un profil donne."""
    if top_k < 1:
        raise ValueError("top_k doit etre >= 1.")
    tax = taxonomy if taxonomy is not None else SkillTaxonomyGraph()
    vec = _build_corpus_vectorizer([profile], opportunities)

    results = [
        evaluate_match(
            profile,
            opp,
            weights=weights,
            constraints=constraints,
            taxonomy=tax,
            vectorizer=vec,
        )
        for opp in opportunities
    ]
    filtered = [res for res in results if res.meets_constraints]
    filtered.sort(
        key=lambda r: (
            -round(r.breakdown.total_score, 8),
            -round(r.breakdown.mandatory_coverage_ratio, 8),
            r.opportunity_id,
        )
    )
    return filtered[:top_k]


def rank_profiles_for_opportunity(
    opportunity: Opportunity,
    profiles: Sequence[Profile],
    top_k: int = 5,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    constraints: MatchConstraints | None = None,
    taxonomy: SkillTaxonomyGraph | None = None,
) -> list[MatchResult]:
    """Classe de maniere deterministe les Top-K profils pour une opportunite donnee."""
    if top_k < 1:
        raise ValueError("top_k doit etre >= 1.")
    tax = taxonomy if taxonomy is not None else SkillTaxonomyGraph()
    vec = _build_corpus_vectorizer(profiles, [opportunity])

    results = [
        evaluate_match(
            prof,
            opportunity,
            weights=weights,
            constraints=constraints,
            taxonomy=tax,
            vectorizer=vec,
        )
        for prof in profiles
    ]
    filtered = [res for res in results if res.meets_constraints]
    filtered.sort(
        key=lambda r: (
            -round(r.breakdown.total_score, 8),
            -round(r.breakdown.mandatory_coverage_ratio, 8),
            r.profile_id,
        )
    )
    return filtered[:top_k]
