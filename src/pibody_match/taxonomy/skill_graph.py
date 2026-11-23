from __future__ import annotations

from typing import TYPE_CHECKING

from pibody_match.domain.skills import SkillClaim, SkillRequirement
from pibody_match.taxonomy.catalog import DEFAULT_SKILL_CATALOG, SkillNode
from pibody_match.taxonomy.synonyms import resolve_skill_id

if TYPE_CHECKING:
    from collections.abc import Iterable


class SkillTaxonomyGraph:
    """Graphe oriente des competences permettant le calcul de proximite semantique."""

    def __init__(self, nodes: Iterable[SkillNode] = DEFAULT_SKILL_CATALOG) -> None:
        self._nodes: dict[str, SkillNode] = {}
        self._children: dict[str, set[str]] = {}
        for node in nodes:
            self._nodes[node.skill_id] = node
            self._children.setdefault(node.skill_id, set())
            if node.parent_id is not None:
                self._children.setdefault(node.parent_id, set()).add(node.skill_id)

    def get_node(self, skill_id: str) -> SkillNode | None:
        """Retourne le noeud canonique associe a un identifiant."""
        return self._nodes.get(resolve_skill_id(skill_id))

    def canonical_info(self, raw_name: str) -> tuple[str, str, str]:
        """Retourne (skill_id, canonical_name, family) pour un libelle brut."""
        skill_id = resolve_skill_id(raw_name)
        node = self._nodes.get(skill_id)
        if node is not None:
            return node.skill_id, node.canonical_name, node.family
        return skill_id, raw_name.strip() or skill_id, "general"

    def similarity(self, source_id: str, target_id: str) -> float:
        """Calcule la proximite taxonomique tau(source, target) dans [0.0, 1.0]."""
        src = resolve_skill_id(source_id)
        tgt = resolve_skill_id(target_id)
        if src == tgt:
            return 1.0
        n_src = self._nodes.get(src)
        n_tgt = self._nodes.get(tgt)
        if n_src is None or n_tgt is None:
            return 0.0
        if n_src.parent_id == tgt or n_tgt.parent_id == src:
            return 0.55
        if n_src.parent_id is not None and n_src.parent_id == n_tgt.parent_id:
            return 0.35
        if n_src.family == n_tgt.family:
            return 0.20
        return 0.0

    def build_claim(
        self,
        raw_name: str,
        proficiency: float,
        years_experience: float = 0.0,
        verified: bool = False,
    ) -> SkillClaim:
        """Construit un SkillClaim normalise via la taxonomie."""
        skill_id, canonical_name, family = self.canonical_info(raw_name)
        return SkillClaim(
            skill_id=skill_id,
            raw_name=raw_name,
            canonical_name=canonical_name,
            family=family,
            proficiency=proficiency,
            years_experience=years_experience,
            verified=verified,
        )

    def build_requirement(
        self,
        raw_name: str,
        min_proficiency: float,
        min_years: float = 0.0,
        weight: float = 1.0,
        mandatory: bool = False,
    ) -> SkillRequirement:
        """Construit un SkillRequirement normalise via la taxonomie."""
        skill_id, canonical_name, family = self.canonical_info(raw_name)
        return SkillRequirement(
            skill_id=skill_id,
            canonical_name=canonical_name,
            family=family,
            min_proficiency=min_proficiency,
            min_years=min_years,
            weight=weight,
            mandatory=mandatory,
        )
