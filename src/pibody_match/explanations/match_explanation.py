from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pibody_match.domain.skills import GapStatus, SkillGapItem

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pibody_match.domain.opportunities import Opportunity
    from pibody_match.domain.profiles import Profile
    from pibody_match.scoring.compatibility import ScoreBreakdown


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    """Justification structuree et lisible d'une recommandation de matching."""

    summary: str
    strengths: tuple[str, ...]
    warnings: tuple[str, ...]
    shared_keywords: tuple[str, ...]
    disclaimer: str = (
        "Indice d'aide a la decision calcule selon les ponderations configurees ; "
        "validation humaine requise."
    )


def build_match_explanation(
    profile: Profile,
    opportunity: Opportunity,
    breakdown: ScoreBreakdown,
    gaps: tuple[SkillGapItem, ...],
    lexical_overlap: Sequence[tuple[str, float]],
) -> MatchExplanation:
    """Produit une explication deterministe a partir du breakdown et des ecarts."""
    strengths: list[str] = []
    warnings: list[str] = []

    for gap in gaps:
        req_pct = round(gap.required_proficiency * 100)
        eff_pct = round(gap.effective_proficiency * 100)
        if gap.status == GapStatus.MATCHED:
            strengths.append(
                f"Competence validee : {gap.canonical_name} ({eff_pct}% vs {req_pct}% requis)"
            )
        elif gap.status == GapStatus.PARTIAL:
            if gap.actual_proficiency == 0.0 and gap.matched_via is not None:
                warnings.append(
                    f"Proximite taxonomique pour {gap.canonical_name} via {gap.matched_via} "
                    f"(credit {round(gap.taxonomic_similarity * 100)}%)"
                )
            else:
                warnings.append(
                    f"Niveau partiel sur {gap.canonical_name} ({eff_pct}% vs {req_pct}% requis)"
                )
        else:
            tag = (
                "Prerequis obligatoire manquant"
                if gap.mandatory
                else "Competence souhaitable absente"
            )
            warnings.append(f"{tag} : {gap.canonical_name}")

    if profile.total_experience_years >= opportunity.min_total_experience:
        strengths.append(
            f"Experience conforme : {profile.total_experience_years:.1f} ans "
            f"(>= {opportunity.min_total_experience:.1f} ans requis)"
        )
    else:
        warnings.append(
            f"Experience inferieure au seuil : {profile.total_experience_years:.1f} ans "
            f"vs {opportunity.min_total_experience:.1f} ans requis"
        )

    if breakdown.objectives_score >= 0.35:
        strengths.append(
            f"Alignement semantique notable ({round(breakdown.objectives_score * 100)}%)"
        )

    keywords = tuple(term for term, _ in lexical_overlap)
    pct = round(breakdown.total_score * 100, 1)
    summary = (
        f"Indice de compatibilite de {pct}% entre {profile.display_name} et "
        f"'{opportunity.title}' (Competences {round(breakdown.skills_score * 100)}%, "
        f"Objectifs {round(breakdown.objectives_score * 100)}%, "
        f"Experience {round(breakdown.experience_score * 100)}%, "
        f"Exigences {round(breakdown.requirements_score * 100)}%)."
    )
    return MatchExplanation(
        summary=summary,
        strengths=tuple(strengths),
        warnings=tuple(warnings),
        shared_keywords=keywords,
    )
