from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pibody_match.domain.constraints import MatchConstraints
from pibody_match.optimizer.ranking import (
    MatchResult,
    _build_corpus_vectorizer,
    evaluate_match,
)
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pibody_match.domain.opportunities import Opportunity
    from pibody_match.domain.profiles import Profile


@dataclass(frozen=True, slots=True)
class GlobalOptimizationReport:
    """Resultat d'une affectation globale maximale sur graphe biparti."""

    assignments: tuple[MatchResult, ...]
    total_global_score: float
    average_score: float
    unassigned_profile_ids: tuple[str, ...]
    unassigned_opportunity_ids: tuple[str, ...]


def _solve_min_cost_rectangular(cost: list[list[float]]) -> list[tuple[int, int]]:
    """Resout le probleme d'affectation minimale sur matrice n x m (n <= m)."""
    n = len(cost)
    m = len(cost[0])
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    pairs: list[tuple[int, int]] = []
    for j in range(1, m + 1):
        if p[j] != 0:
            pairs.append((p[j] - 1, j - 1))
    return pairs


def optimize_global_assignment(
    profiles: Sequence[Profile],
    opportunities: Sequence[Opportunity],
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    constraints: MatchConstraints | None = None,
    taxonomy: SkillTaxonomyGraph | None = None,
) -> GlobalOptimizationReport:
    """Maximise la somme globale des scores S(p_i, o_j) via l'algorithme Hongrois."""
    if not profiles or not opportunities:
        return GlobalOptimizationReport(
            assignments=(),
            total_global_score=0.0,
            average_score=0.0,
            unassigned_profile_ids=tuple(p.profile_id for p in profiles),
            unassigned_opportunity_ids=tuple(o.opportunity_id for o in opportunities),
        )

    active_constraints = constraints if constraints is not None else MatchConstraints()
    tax = taxonomy if taxonomy is not None else SkillTaxonomyGraph()
    vec = _build_corpus_vectorizer(profiles, opportunities)

    # Expansion des postes selon la capacite C_o de chaque opportunite
    slots: list[Opportunity] = []
    for opp in opportunities:
        for _ in range(opp.capacity):
            slots.append(opp)

    pair_cache: dict[tuple[str, str], MatchResult] = {}
    for prof in profiles:
        for opp in opportunities:
            pair_cache[(prof.profile_id, opp.opportunity_id)] = evaluate_match(
                prof,
                opp,
                weights=weights,
                constraints=active_constraints,
                taxonomy=tax,
                vectorizer=vec,
            )

    n_rows = len(profiles)
    n_cols = len(slots)
    forbidden_cost = 100.0

    raw_cost: list[list[float]] = []
    for prof in profiles:
        row: list[float] = []
        for opp in slots:
            res = pair_cache[(prof.profile_id, opp.opportunity_id)]
            row.append(1.0 - res.breakdown.total_score if res.meets_constraints else forbidden_cost)
        raw_cost.append(row)

    if n_rows <= n_cols:
        matched_indices = _solve_min_cost_rectangular(raw_cost)
    else:
        transposed = [[raw_cost[r][c] for r in range(n_rows)] for c in range(n_cols)]
        matched_indices = [(r, c) for c, r in _solve_min_cost_rectangular(transposed)]

    selected: list[MatchResult] = []
    assigned_profs: set[str] = set()
    assigned_opps: set[str] = set()

    for r_idx, c_idx in matched_indices:
        prof = profiles[r_idx]
        opp = slots[c_idx]
        res = pair_cache[(prof.profile_id, opp.opportunity_id)]
        if res.meets_constraints:
            selected.append(res)
            assigned_profs.add(prof.profile_id)
            assigned_opps.add(opp.opportunity_id)

    selected.sort(
        key=lambda r: (-round(r.breakdown.total_score, 8), r.profile_id, r.opportunity_id)
    )
    total = round(sum(r.breakdown.total_score for r in selected), 6)
    avg = round(total / len(selected), 6) if selected else 0.0

    return GlobalOptimizationReport(
        assignments=tuple(selected),
        total_global_score=total,
        average_score=avg,
        unassigned_profile_ids=tuple(
            p.profile_id for p in profiles if p.profile_id not in assigned_profs
        ),
        unassigned_opportunity_ids=tuple(
            o.opportunity_id for o in opportunities if o.opportunity_id not in assigned_opps
        ),
    )
