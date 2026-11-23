from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from pibody_match.domain.profiles import SENSITIVE_ATTRIBUTE_BLOCKLIST, Profile
from pibody_match.scoring.compatibility import compute_compatibility
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pibody_match.domain.opportunities import Opportunity


def audit_profile_privacy(profile: Profile) -> list[str]:
    """Verifie qu'aucun attribut sensible interdit ne figure dans un profil."""
    violations: list[str] = []
    for tag in profile.public_tags:
        key = tag.strip().lower().split(":", 1)[0]
        if key in SENSITIVE_ATTRIBUTE_BLOCKLIST:
            violations.append(tag)
    return violations


def check_score_invariance_under_anonymization(
    profile: Profile,
    opportunity: Opportunity,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
) -> bool:
    """Garantit que l'anonymisation de l'identite ne modifie jamais le score."""
    anonymized = replace(
        profile,
        profile_id="anon_candidate",
        display_name="Candidat Anonyme",
    )
    b_orig, _, _ = compute_compatibility(profile, opportunity, weights=weights)
    b_anon, _, _ = compute_compatibility(anonymized, opportunity, weights=weights)
    return b_orig == b_anon


def compute_selection_parity(
    selected_profile_ids: Sequence[str],
    cohort_by_profile: Mapping[str, str],
) -> dict[str, float]:
    """Calcule le taux de selection par cohorte anonyme pour l'audit d'equite."""
    selected_set = set(selected_profile_ids)
    totals: dict[str, int] = {}
    chosen: dict[str, int] = {}

    for pid, cohort in cohort_by_profile.items():
        totals[cohort] = totals.get(cohort, 0) + 1
        if pid in selected_set:
            chosen[cohort] = chosen.get(cohort, 0) + 1

    return {
        cohort: round(chosen.get(cohort, 0) / count, 6)
        for cohort, count in sorted(totals.items())
        if count > 0
    }
