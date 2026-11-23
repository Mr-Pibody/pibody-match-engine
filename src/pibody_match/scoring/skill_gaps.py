from __future__ import annotations

from typing import TYPE_CHECKING

from pibody_match.domain.skills import GapStatus, SkillGapItem

if TYPE_CHECKING:
    from pibody_match.domain.opportunities import Opportunity
    from pibody_match.domain.profiles import Profile
    from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph


def evaluate_skill_gaps(
    profile: Profile,
    opportunity: Opportunity,
    taxonomy: SkillTaxonomyGraph,
) -> tuple[SkillGapItem, ...]:
    """Evalue chaque exigence de l'opportunite par rapport aux competences du profil."""
    owned = profile.skill_map()
    gaps: list[SkillGapItem] = []

    for req in opportunity.requirements:
        direct = owned.get(req.skill_id)
        if direct is not None:
            bonus = 0.05 if direct.verified else 0.0
            effective = min(1.0, direct.proficiency + bonus)
            ratio = min(1.0, effective / req.min_proficiency) if req.min_proficiency > 0.0 else 1.0
            status = GapStatus.MATCHED if effective >= req.min_proficiency else GapStatus.PARTIAL
            gaps.append(
                SkillGapItem(
                    skill_id=req.skill_id,
                    canonical_name=req.canonical_name,
                    family=req.family,
                    status=status,
                    mandatory=req.mandatory,
                    required_proficiency=req.min_proficiency,
                    actual_proficiency=direct.proficiency,
                    effective_proficiency=round(effective, 6),
                    coverage_ratio=round(ratio, 6),
                    matched_via=direct.canonical_name,
                    taxonomic_similarity=1.0,
                )
            )
            continue

        best_claim = None
        best_sim = 0.0
        for claim in profile.skills:
            sim = taxonomy.similarity(claim.skill_id, req.skill_id)
            if sim > best_sim or (
                sim == best_sim
                and sim > 0.0
                and best_claim is not None
                and claim.proficiency > best_claim.proficiency
            ):
                best_sim = sim
                best_claim = claim

        if best_claim is not None and best_sim > 0.0:
            effective = min(1.0, best_claim.proficiency * best_sim)
            ratio = (
                min(1.0, effective / req.min_proficiency) if req.min_proficiency > 0.0 else best_sim
            )
            gaps.append(
                SkillGapItem(
                    skill_id=req.skill_id,
                    canonical_name=req.canonical_name,
                    family=req.family,
                    status=GapStatus.PARTIAL,
                    mandatory=req.mandatory,
                    required_proficiency=req.min_proficiency,
                    actual_proficiency=0.0,
                    effective_proficiency=round(effective, 6),
                    coverage_ratio=round(ratio, 6),
                    matched_via=best_claim.canonical_name,
                    taxonomic_similarity=best_sim,
                )
            )
        else:
            gaps.append(
                SkillGapItem(
                    skill_id=req.skill_id,
                    canonical_name=req.canonical_name,
                    family=req.family,
                    status=GapStatus.MISSING,
                    mandatory=req.mandatory,
                    required_proficiency=req.min_proficiency,
                    actual_proficiency=0.0,
                    effective_proficiency=0.0,
                    coverage_ratio=0.0,
                    matched_via=None,
                    taxonomic_similarity=0.0,
                )
            )

    return tuple(gaps)
