from __future__ import annotations

from pibody_match.domain.universal import (
    EntityKind,
    Need,
    TeamComposition,
    UniversalMatch,
    UserEntity,
)


def compose_optimal_team(
    need: Need,
    matches: list[UniversalMatch],
    entities_by_id: dict[str, UserEntity],
) -> TeamComposition:
    """Assemble une equipe complementaire couvrant au mieux les besoins d'un projet."""
    target_count = max(2, min(need.team_size, 5))
    eligible = [
        m
        for m in matches
        if entities_by_id[m.entity_id].kind in {EntityKind.PERSON, EntityKind.MENTOR}
    ]
    selected: list[UniversalMatch] = []
    covered: set[str] = set()
    families_covered: set[str] = set()

    while eligible and len(selected) < target_count:
        best_item: UniversalMatch | None = None
        best_gain = -1.0
        for cand in eligible:
            ent = entities_by_id[cand.entity_id]
            new_skills = set(cand.matched_skills) - covered
            new_fams = {c.family for c in ent.capabilities} - families_covered
            gain = len(new_skills) * 0.45 + len(new_fams) * 0.25 + cand.combined_score * 0.30
            if gain > best_gain:
                best_gain = gain
                best_item = cand
        if best_item is None:
            break
        selected.append(best_item)
        covered.update(best_item.matched_skills)
        families_covered.update(c.family for c in entities_by_id[best_item.entity_id].capabilities)
        eligible = [m for m in eligible if m.entity_id != best_item.entity_id]

    req_set = set(need.required_skills)
    cov_ratio = len(covered & req_set) / max(1, len(req_set))
    synergy = min(1.0, len(families_covered) / max(1, target_count + 1))
    avg_member = sum(m.combined_score for m in selected) / max(1, len(selected))
    overall = min(1.0, 0.50 * cov_ratio + 0.25 * synergy + 0.25 * avg_member)

    uncovered = tuple(s for s in need.required_skills if s not in covered)
    names = ", ".join(m.entity_name for m in selected)
    rationale = (
        f"Equipe de {len(selected)} membres ({names}) couvrant {cov_ratio * 100:.0f}% "
        f"des competences requises sur {len(families_covered)} domaines complementaires."
    )
    return TeamComposition(
        need_id=need.need_id,
        members=tuple(selected),
        collective_coverage=round(cov_ratio, 4),
        synergy_score=round(synergy, 4),
        overall_score=round(overall, 4),
        covered_skills=tuple(sorted(covered)),
        uncovered_skills=uncovered,
        rationale=rationale,
    )
