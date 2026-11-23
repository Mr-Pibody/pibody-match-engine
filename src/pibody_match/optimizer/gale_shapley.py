from __future__ import annotations

from collections import deque
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
class StableMatchingReport:
    """Resultat d'un appariement stable bilaterale (Gale-Shapley)."""

    assignments: tuple[MatchResult, ...]
    is_stable: bool
    total_score: float
    unmatched_profile_ids: tuple[str, ...]


def _rank_key(res: MatchResult, tie_id: str) -> tuple[float, float, str]:
    return (
        -round(res.breakdown.total_score, 8),
        -round(res.breakdown.mandatory_coverage_ratio, 8),
        tie_id,
    )


def compute_stable_matching(
    profiles: Sequence[Profile],
    opportunities: Sequence[Opportunity],
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    constraints: MatchConstraints | None = None,
    taxonomy: SkillTaxonomyGraph | None = None,
) -> StableMatchingReport:
    """Calcule un appariement stable sans paire bloquante via Gale-Shapley."""
    if not profiles or not opportunities:
        return StableMatchingReport(
            assignments=(),
            is_stable=True,
            total_score=0.0,
            unmatched_profile_ids=tuple(p.profile_id for p in profiles),
        )

    active_constraints = constraints if constraints is not None else MatchConstraints()
    tax = taxonomy if taxonomy is not None else SkillTaxonomyGraph()
    vec = _build_corpus_vectorizer(profiles, opportunities)

    pair_results: dict[tuple[str, str], MatchResult] = {}
    for prof in profiles:
        for opp in opportunities:
            pair_results[(prof.profile_id, opp.opportunity_id)] = evaluate_match(
                prof,
                opp,
                weights=weights,
                constraints=active_constraints,
                taxonomy=tax,
                vectorizer=vec,
            )

    prof_prefs: dict[str, list[str]] = {}
    for prof in profiles:
        valid = [
            opp.opportunity_id
            for opp in opportunities
            if pair_results[(prof.profile_id, opp.opportunity_id)].meets_constraints
        ]
        valid.sort(key=lambda oid: _rank_key(pair_results[(prof.profile_id, oid)], oid))
        prof_prefs[prof.profile_id] = valid

    opp_rank: dict[str, dict[str, int]] = {}
    opp_cap: dict[str, int] = {}
    for opp in opportunities:
        opp_cap[opp.opportunity_id] = opp.capacity
        valid_p = [
            prof.profile_id
            for prof in profiles
            if pair_results[(prof.profile_id, opp.opportunity_id)].meets_constraints
        ]
        valid_p.sort(key=lambda pid: _rank_key(pair_results[(pid, opp.opportunity_id)], pid))
        opp_rank[opp.opportunity_id] = {pid: idx for idx, pid in enumerate(valid_p)}

    next_proposal_idx: dict[str, int] = {p.profile_id: 0 for p in profiles}
    held_by_opp: dict[str, list[str]] = {o.opportunity_id: [] for o in opportunities}
    free_queue: deque[str] = deque(p.profile_id for p in profiles)

    while free_queue:
        pid = free_queue.popleft()
        prefs = prof_prefs[pid]
        idx = next_proposal_idx[pid]
        if idx >= len(prefs):
            continue
        oid = prefs[idx]
        next_proposal_idx[pid] = idx + 1

        current = held_by_opp[oid]
        cap = opp_cap[oid]
        if len(current) < cap:
            current.append(pid)
        else:
            worst_pid = max(current, key=lambda cand: opp_rank[oid][cand])
            if opp_rank[oid][pid] < opp_rank[oid][worst_pid]:
                current.remove(worst_pid)
                current.append(pid)
                free_queue.append(worst_pid)
            else:
                free_queue.append(pid)

    assigned_opp_for_prof: dict[str, str] = {}
    final_results: list[MatchResult] = []
    for oid, pids in held_by_opp.items():
        for pid in pids:
            assigned_opp_for_prof[pid] = oid
            final_results.append(pair_results[(pid, oid)])

    stable = verify_stability(prof_prefs, opp_rank, opp_cap, assigned_opp_for_prof, held_by_opp)
    final_results.sort(
        key=lambda r: (-round(r.breakdown.total_score, 8), r.profile_id, r.opportunity_id)
    )
    total = round(sum(r.breakdown.total_score for r in final_results), 6)

    return StableMatchingReport(
        assignments=tuple(final_results),
        is_stable=stable,
        total_score=total,
        unmatched_profile_ids=tuple(
            p.profile_id for p in profiles if p.profile_id not in assigned_opp_for_prof
        ),
    )


def verify_stability(
    prof_prefs: dict[str, list[str]],
    opp_rank: dict[str, dict[str, int]],
    opp_cap: dict[str, int],
    assigned_opp: dict[str, str],
    held_by_opp: dict[str, list[str]],
) -> bool:
    """Verifie formellement l'absence de toute paire bloquante (p, o)."""
    for pid, prefs in prof_prefs.items():
        current_oid = assigned_opp.get(pid)
        limit = prefs.index(current_oid) if current_oid in prefs else len(prefs)
        for preferred_oid in prefs[:limit]:
            if pid not in opp_rank[preferred_oid]:
                continue
            holders = held_by_opp[preferred_oid]
            if len(holders) < opp_cap[preferred_oid]:
                return False
            worst_holder_rank = max(opp_rank[preferred_oid][h] for h in holders)
            if opp_rank[preferred_oid][pid] < worst_holder_rank:
                return False
    return True
