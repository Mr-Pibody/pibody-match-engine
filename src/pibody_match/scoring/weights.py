from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Ponderations normalisees des quatre piliers de compatibilite (somme == 1)."""

    skills: float = 0.40
    objectives: float = 0.20
    experience: float = 0.20
    requirements: float = 0.20

    def __post_init__(self) -> None:
        values = (self.skills, self.objectives, self.experience, self.requirements)
        if any(w < 0.0 for w in values):
            raise ValueError("Toutes les ponderations doivent etre >= 0.0.")
        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"La somme des ponderations doit valoir 1.0 (recu : {total:.6f}).")


DEFAULT_WEIGHTS = ScoreWeights()
TECH_HEAVY_WEIGHTS = ScoreWeights(skills=0.55, objectives=0.15, experience=0.15, requirements=0.15)
VISION_HEAVY_WEIGHTS = ScoreWeights(
    skills=0.30, objectives=0.35, experience=0.15, requirements=0.20
)
