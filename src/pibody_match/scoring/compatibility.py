from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pibody_match.domain.skills import GapStatus, SkillGapItem
from pibody_match.nlp.similarity import cosine_similarity, explain_lexical_overlap
from pibody_match.nlp.vectorization import TfidfVectorizer
from pibody_match.scoring.skill_gaps import evaluate_skill_gaps
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

if TYPE_CHECKING:
    from pibody_match.domain.opportunities import Opportunity
    from pibody_match.domain.profiles import Profile


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Decomposition chiffree et verifiable du score de compatibilite S(p, o)."""

    skills_score: float
    objectives_score: float
    experience_score: float
    requirements_score: float
    weighted_skills: float
    weighted_objectives: float
    weighted_experience: float
    weighted_requirements: float
    total_score: float
    mandatory_coverage_ratio: float
    missing_mandatory_skills: tuple[str, ...]


def compute_compatibility(
    profile: Profile,
    opportunity: Opportunity,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    taxonomy: SkillTaxonomyGraph | None = None,
    vectorizer: TfidfVectorizer | None = None,
) -> tuple[ScoreBreakdown, tuple[SkillGapItem, ...], list[tuple[str, float]]]:
    """Calcule le score asymetrique S(p, o) dans [0, 1] et ses justifications."""
    tax = taxonomy if taxonomy is not None else SkillTaxonomyGraph()
    gaps = evaluate_skill_gaps(profile, opportunity, tax)

    total_req_weight = sum(req.weight for req in opportunity.requirements)
    weighted_gap_sum = sum(
        req.weight * gap.coverage_ratio
        for req, gap in zip(opportunity.requirements, gaps, strict=True)
    )
    s_skills = min(1.0, max(0.0, weighted_gap_sum / total_req_weight))

    prof_text = f"{profile.headline} {profile.objectives_text}"
    opp_text = f"{opportunity.title} {opportunity.description_text} {opportunity.objectives_text}"
    vec = vectorizer if vectorizer is not None else TfidfVectorizer().fit([prof_text, opp_text])
    vec_p = vec.transform(prof_text)
    vec_o = vec.transform(opp_text)
    s_objectives = cosine_similarity(vec_p, vec_o)
    overlap = explain_lexical_overlap(vec_p, vec_o, top_n=5)

    global_exp_ratio = (
        min(1.0, profile.total_experience_years / opportunity.min_total_experience)
        if opportunity.min_total_experience > 0.0
        else 1.0
    )
    owned = profile.skill_map()
    exp_reqs = [req for req in opportunity.requirements if req.min_years > 0.0]
    if exp_reqs:
        per_skill_exp: list[float] = []
        for req in exp_reqs:
            claim = owned.get(req.skill_id)
            years = claim.years_experience if claim is not None else 0.0
            per_skill_exp.append(min(1.0, years / req.min_years))
        skill_exp_ratio = sum(per_skill_exp) / len(per_skill_exp)
    else:
        skill_exp_ratio = 1.0
    s_experience = min(1.0, max(0.0, 0.60 * global_exp_ratio + 0.40 * skill_exp_ratio))

    mandatory_pairs = [
        (req, gap) for req, gap in zip(opportunity.requirements, gaps, strict=True) if req.mandatory
    ]
    if mandatory_pairs:
        mandatory_cov = sum(gap.coverage_ratio for _, gap in mandatory_pairs) / len(mandatory_pairs)
        missing_mand = tuple(
            gap.canonical_name for _, gap in mandatory_pairs if gap.status == GapStatus.MISSING
        )
    else:
        mandatory_cov = 1.0
        missing_mand = ()
    s_requirements = min(1.0, max(0.0, 0.75 * mandatory_cov + 0.25 * profile.availability_ratio))

    w_sk = weights.skills * s_skills
    w_ob = weights.objectives * s_objectives
    w_ex = weights.experience * s_experience
    w_rq = weights.requirements * s_requirements
    total = min(1.0, max(0.0, w_sk + w_ob + w_ex + w_rq))

    breakdown = ScoreBreakdown(
        skills_score=round(s_skills, 6),
        objectives_score=round(s_objectives, 6),
        experience_score=round(s_experience, 6),
        requirements_score=round(s_requirements, 6),
        weighted_skills=round(w_sk, 6),
        weighted_objectives=round(w_ob, 6),
        weighted_experience=round(w_ex, 6),
        weighted_requirements=round(w_rq, 6),
        total_score=round(total, 6),
        mandatory_coverage_ratio=round(mandatory_cov, 6),
        missing_mandatory_skills=missing_mand,
    )
    return breakdown, gaps, overlap
