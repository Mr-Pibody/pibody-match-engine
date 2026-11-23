from __future__ import annotations

import pytest

from pibody_match.datasets.reference import build_reference_dataset
from pibody_match.domain.constraints import MatchConstraints
from pibody_match.domain.profiles import Profile
from pibody_match.domain.skills import GapStatus, SeniorityLevel
from pibody_match.nlp.similarity import cosine_similarity, explain_lexical_overlap
from pibody_match.nlp.vectorization import TfidfVectorizer
from pibody_match.optimizer.ranking import evaluate_match, rank_profiles_for_opportunity
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph


def test_taxonomy_alias_and_hierarchy() -> None:
    tax = SkillTaxonomyGraph()
    assert tax.canonical_info("py")[1] == "Python"
    assert tax.canonical_info("ReactJS")[1] == "React"
    assert tax.similarity("FastAPI", "Python") > 0.5
    assert tax.similarity("Python", "Flutter") == 0.0


def test_tfidf_similarity_bounds_and_overlap() -> None:
    docs = [
        "developpement api python fastapi machine learning",
        "infrastructure cloud aws kubernetes docker ci cd",
    ]
    vec = TfidfVectorizer().fit(docs)
    v1 = vec.transform("api python machine learning")
    v2 = vec.transform("python fastapi production")
    sim = cosine_similarity(v1, v2)
    assert 0.0 <= sim <= 1.0
    assert sim > 0.2
    overlap_terms = [term for term, _ in explain_lexical_overlap(v1, v2)]
    assert "python" in overlap_terms


def test_weights_validation_sum_to_one() -> None:
    with pytest.raises(ValueError):
        ScoreWeights(skills=0.5, objectives=0.5, experience=0.2, requirements=0.2)
    assert abs(DEFAULT_WEIGHTS.skills + DEFAULT_WEIGHTS.objectives - 0.6) < 1e-9


def test_explainable_match_and_strict_mandatory() -> None:
    profiles, opportunities, _ = build_reference_dataset()
    opp_ai = next(o for o in opportunities if o.opportunity_id == "opp_ai_backend")
    amina = next(p for p in profiles if p.profile_id == "prof_01")
    sarah = next(p for p in profiles if p.profile_id == "prof_05")

    res_amina = evaluate_match(amina, opp_ai)
    assert res_amina.breakdown.total_score > 0.80
    assert any(g.status == GapStatus.MATCHED for g in res_amina.skill_gaps)
    assert res_amina.explanation.summary

    strict_ranked = rank_profiles_for_opportunity(
        opp_ai,
        profiles,
        top_k=6,
        constraints=MatchConstraints(strict_mandatory=True),
    )
    ranked_ids = {r.profile_id for r in strict_ranked}
    assert amina.profile_id in ranked_ids
    assert sarah.profile_id not in ranked_ids


def test_profile_blocks_sensitive_tags() -> None:
    tax = SkillTaxonomyGraph()
    with pytest.raises(ValueError):
        Profile(
            profile_id="prof_bad",
            display_name="Test",
            headline="Dev",
            seniority=SeniorityLevel.JUNIOR,
            skills=(tax.build_claim("Python", 0.8, 1.0),),
            objectives_text="Coder",
            total_experience_years=1.0,
            public_tags=("gender:female",),
        )
