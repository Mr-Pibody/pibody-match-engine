from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pibody_match.domain.constraints import HumanDecision

if TYPE_CHECKING:
    from pibody_match.optimizer.ranking import MatchResult
    from pibody_match.scoring.weights import ScoreWeights


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Enregistrement immuable de tracabilite d'une recommandation et sa revue humaine."""

    audit_id: str
    match_id: str
    profile_id: str
    opportunity_id: str
    total_score: float
    weights_snapshot: dict[str, float]
    decision: HumanDecision
    reviewer_note: str
    timestamp_utc: str


class AuditTrail:
    """Journal d'audit deterministe pour la gouvernance Human-in-the-loop."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        """Retourne l'historique immuable des decisions auditees."""
        return tuple(self._records)

    def record_decision(
        self,
        match: MatchResult,
        weights: ScoreWeights,
        decision: HumanDecision = HumanDecision.PENDING,
        reviewer_note: str = "",
    ) -> AuditRecord:
        """Ajoute une trace d'audit horodatee pour un resultat de matching."""
        entry = AuditRecord(
            audit_id=f"aud_{len(self._records) + 1:04d}_{match.match_id}",
            match_id=match.match_id,
            profile_id=match.profile_id,
            opportunity_id=match.opportunity_id,
            total_score=match.breakdown.total_score,
            weights_snapshot={
                "skills": weights.skills,
                "objectives": weights.objectives,
                "experience": weights.experience,
                "requirements": weights.requirements,
            },
            decision=decision,
            reviewer_note=reviewer_note,
            timestamp_utc=datetime.now(UTC).isoformat(),
        )
        self._records.append(entry)
        return entry

    def export_json(self) -> str:
        """Exporte le journal d'audit complet au format JSON indente."""
        payload = [asdict(rec) for rec in self._records]
        return json.dumps(payload, indent=2, ensure_ascii=False)
