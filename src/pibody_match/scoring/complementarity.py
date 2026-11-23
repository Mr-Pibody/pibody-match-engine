from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from pibody_match.domain.universal import (
    EntityKind,
    IntentType,
    Need,
    SkillPathStep,
    UniversalMatch,
    UserEntity,
)
from pibody_match.nlp.similarity import cosine_similarity

if TYPE_CHECKING:
    from pibody_match.nlp.vectorization import TfidfVectorizer
    from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph


def evaluate_universal_match(
    need: Need,
    entity: UserEntity,
    taxonomy: SkillTaxonomyGraph,
    vectorizer: TfidfVectorizer,
) -> UniversalMatch:
    """Evalue une entite sur 6 dimensions : pertinence, skills, synergie, dispo, buts."""
    vec_need = vectorizer.transform(f"{need.raw_query} {need.primary_goal}")
    vec_entity = vectorizer.transform(
        f"{entity.headline} {entity.bio_and_goals} "
        + " ".join(c.canonical_name for c in entity.capabilities)
    )
    need_relevance = cosine_similarity(vec_need, vec_entity)

    matched: list[str] = []
    missing: list[str] = []
    skill_scores: list[float] = []

    for req_skill in need.required_skills:
        best = 0.0
        for cap in entity.capabilities:
            sim = taxonomy.similarity(req_skill, cap.canonical_name)
            weighted = sim * (0.65 + 0.35 * cap.level)
            if weighted > best:
                best = weighted
        skill_scores.append(min(1.0, best))
        if best >= 0.45:
            matched.append(req_skill)
        else:
            missing.append(req_skill)

    skills_score = sum(skill_scores) / max(1, len(skill_scores))
    exp_ratio = (
        1.0 if need.min_experience <= 0 else min(1.0, entity.experience_years / need.min_experience)
    )
    availability_score = min(
        1.0, entity.availability_hours_week / max(1, need.requested_hours_week)
    )
    goal_alignment = min(1.0, 0.55 * need_relevance + 0.45 * exp_ratio)

    req_families: set[str] = set()
    for s in need.required_skills:
        with contextlib.suppress(KeyError):
            req_families.add(taxonomy.canonical_info(s)[2])
    ent_families = {c.family for c in entity.capabilities}
    novel_families = ent_families - req_families
    teaching_edge = 0.22 if any(c.can_teach for c in entity.capabilities) else 0.0
    collab_edge = 0.18 if entity.open_to_collaborate else 0.0
    complementarity = min(
        1.0,
        0.24 * len(novel_families) + 0.12 * len(ent_families) + teaching_edge + collab_edge,
    )

    forward_fit = min(
        1.0,
        0.48 * skills_score
        + 0.22 * need_relevance
        + 0.15 * goal_alignment
        + (0.15 if entity.kind in need.target_kinds else 0.0),
    )

    reverse_interest = 0.35
    if need.intent in {IntentType.FIND_MENTOR, IntentType.LEARN} and entity.open_to_mentor:
        reverse_interest += 0.45
    if (
        need.intent in {IntentType.BUILD_TEAM, IntentType.JOIN_PROJECT}
        and entity.open_to_collaborate
    ):
        reverse_interest += 0.40
    if entity.universe == need.universe:
        reverse_interest += 0.20
    reverse_interest = min(1.0, reverse_interest)

    reciprocity = (
        (2.0 * forward_fit * reverse_interest) / (forward_fit + reverse_interest)
        if (forward_fit + reverse_interest) > 0
        else 0.0
    )

    if need.intent == IntentType.BUILD_TEAM:
        combined = (
            0.30 * skills_score
            + 0.28 * complementarity
            + 0.17 * reciprocity
            + 0.15 * availability_score
            + 0.10 * need_relevance
        )
    elif need.intent in {IntentType.FIND_MENTOR, IntentType.LEARN}:
        combined = (
            0.32 * skills_score
            + 0.26 * reciprocity
            + 0.18 * need_relevance
            + 0.14 * complementarity
            + 0.10 * availability_score
        )
    else:
        combined = (
            0.35 * skills_score
            + 0.22 * need_relevance
            + 0.18 * reciprocity
            + 0.15 * complementarity
            + 0.10 * availability_score
        )

    is_serendipitous = (
        entity.kind not in need.target_kinds and (len(novel_families) >= 1 or skills_score >= 0.4)
    ) or (entity.universe != need.universe and combined >= 0.48)
    domains = ", ".join(sorted(novel_families or ent_families))
    discovery_reason = (
        f"Passerelle inter-univers ({entity.universe.value}) apportant {domains}"
        if is_serendipitous
        else f"Alignement direct dans {entity.universe.value}"
    )

    reason_parts = [f"{entity.name} ({entity.kind.value}) : {combined * 100:.0f}% global."]
    if matched:
        reason_parts.append(f"Couvre {', '.join(matched)}.")
    if novel_families:
        reason_parts.append(f"Synergie en {', '.join(sorted(novel_families))}.")
    if missing:
        reason_parts.append(f"A renforcer : {', '.join(missing)}.")

    dimensions = {
        "pertinence_besoin": round(need_relevance, 4),
        "competences": round(skills_score, 4),
        "complementarite": round(complementarity, 4),
        "disponibilite": round(availability_score, 4),
        "alignement_objectifs": round(goal_alignment, 4),
        "reciprocite": round(reciprocity, 4),
    }
    return UniversalMatch(
        entity_id=entity.entity_id,
        entity_name=entity.name,
        entity_kind=entity.kind,
        universe=entity.universe,
        headline=entity.headline,
        compatibility_score=round(forward_fit, 4),
        complementarity_score=round(complementarity, 4),
        reciprocity_score=round(reciprocity, 4),
        combined_score=round(min(1.0, combined), 4),
        matched_skills=tuple(matched),
        missing_skills=tuple(missing),
        is_serendipitous=is_serendipitous,
        discovery_reason=discovery_reason,
        explanation=" ".join(reason_parts),
        dimensions=dimensions,
    )


def build_skill_pathways(
    need: Need,
    matches: list[UniversalMatch],
    catalog: list[UserEntity],
) -> list[SkillPathStep]:
    """Construit des parcours de progression pour combler les competences manquantes."""
    missing_pool: list[str] = []
    for m in matches[:3]:
        for s in m.missing_skills:
            if s not in missing_pool:
                missing_pool.append(s)
    if not missing_pool and need.required_skills:
        missing_pool = [need.required_skills[-1]]

    steps: list[SkillPathStep] = []
    for skill in missing_pool[:3]:
        res = next(
            (
                e.name
                for e in catalog
                if e.kind == EntityKind.RESOURCE
                and any(c.canonical_name == skill for c in e.capabilities)
            ),
            "Atelier Pratique Pibody Academy",
        )
        mentor = next(
            (
                e.name
                for e in catalog
                if e.open_to_mentor and any(c.canonical_name == skill for c in e.capabilities)
            ),
            "Amina Diallo (Mentore IA)",
        )
        proj = next(
            (
                e.name
                for e in catalog
                if e.kind in {EntityKind.PROJECT, EntityKind.COMMUNITY}
                and any(c.canonical_name == skill for c in e.capabilities)
            ),
            "Communaute Tech Builders",
        )
        steps.append(
            SkillPathStep(
                missing_skill=skill,
                resource_name=res,
                mentor_name=mentor,
                practice_project=proj,
                projected_gain=0.18,
                rationale=(
                    f"Valider {skill} via '{res}' avec l'appui de {mentor}, "
                    f"puis appliquer sur '{proj}' (+18% de compatibilite estimee)."
                ),
            )
        )
    return steps


def build_relationship_graph(
    need: Need,
    matches: list[UniversalMatch],
    catalog: list[UserEntity],
) -> dict[str, Any]:
    """Genere les noeuds et liens du Pibody Relationship Graph."""
    nodes: list[dict[str, str]] = [
        {"id": "need_root", "label": "Besoin Actif", "type": "need"},
    ]
    links: list[dict[str, Any]] = []
    seen_nodes = {"need_root"}

    for skill in need.required_skills:
        sid = f"skill_{skill}"
        if sid not in seen_nodes:
            nodes.append({"id": sid, "label": skill, "type": "skill"})
            seen_nodes.add(sid)
        links.append({"source": "need_root", "target": sid, "weight": 1.0, "label": "requiert"})

    entity_map = {e.entity_id: e for e in catalog}
    for m in matches[:6]:
        nodes.append({"id": m.entity_id, "label": m.entity_name, "type": m.entity_kind.value})
        links.append(
            {
                "source": "need_root",
                "target": m.entity_id,
                "weight": m.combined_score,
                "label": f"{int(m.combined_score * 100)}%",
            }
        )
        ent = entity_map.get(m.entity_id)
        if ent:
            for cap in ent.capabilities[:2]:
                sid = f"skill_{cap.canonical_name}"
                if sid not in seen_nodes:
                    nodes.append({"id": sid, "label": cap.canonical_name, "type": "skill"})
                    seen_nodes.add(sid)
                links.append(
                    {
                        "source": m.entity_id,
                        "target": sid,
                        "weight": cap.level,
                        "label": "maitrise",
                    }
                )
    return {"nodes": nodes, "links": links}
