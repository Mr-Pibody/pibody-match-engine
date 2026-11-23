from __future__ import annotations

import re
import unicodedata

from pibody_match.domain.universal import EntityKind, IntentType, Need, Universe
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

WORD_NUMBERS: dict[str, int] = {
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "two": 2,
    "three": 3,
    "four": 4,
}


def _clean_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    no_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9+#/]+", " ", no_accents).strip()


class NeedParser:
    """Analyse un besoin exprime en langage naturel et genere des clarifications."""

    def __init__(self, taxonomy: SkillTaxonomyGraph | None = None) -> None:
        self.taxonomy = taxonomy or SkillTaxonomyGraph()

    def _extract_skills(self, raw_query: str) -> tuple[str, ...]:
        tokens = _clean_text(raw_query).split()
        found: list[str] = []
        candidates = list(tokens) + [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
        for term in candidates:
            node = self.taxonomy.get_node(term)
            if node is not None and node.canonical_name not in found:
                found.append(node.canonical_name)
        if not found:
            lowered = _clean_text(raw_query)
            if "educat" in lowered or "plateforme" in lowered:
                found.extend(["Python", "React", "UI/UX Design"])
            elif "ia" in lowered or "intelligence artificielle" in lowered:
                found.extend(["Python", "Machine Learning"])
            pass
        return tuple(found)

    def _extract_team_size(self, lowered: str) -> int:
        digit_match = re.search(
            r"\b([2-6])\s*(?:personnes|membres|profils|devs|collaborateurs)", lowered
        )
        if digit_match:
            return int(digit_match.group(1))
        for word, val in WORD_NUMBERS.items():
            if re.search(rf"\b{word}\s+(?:personnes|membres|profils|collaborateurs)", lowered):
                return val
        return 1

    def parse(self, raw_query: str, need_id: str = "need_live") -> Need:
        """Transforme une requete libre en objet Need avec questions de clarification."""
        lowered = _clean_text(raw_query)
        skills = self._extract_skills(raw_query)
        team_size = self._extract_team_size(lowered)
        targets: tuple[EntityKind, ...]

        if any(k in lowered for k in ("mentor", "accompagner", "m aider", "progression")):
            intent = IntentType.FIND_MENTOR
            universe = Universe.MENTORSHIP
            targets = (EntityKind.MENTOR, EntityKind.PERSON, EntityKind.RESOURCE)
            goal = "Trouver un mentor et un cadre d'accompagnement personnalise"
            min_exp, req_hours = 3.0, 6
        elif any(k in lowered for k in ("apprendre", "debuter", "formation", "cours")):
            intent = IntentType.LEARN
            universe = Universe.LEARNING
            targets = (EntityKind.RESOURCE, EntityKind.MENTOR, EntityKind.COMMUNITY)
            goal = "Acquerir de nouvelles competences via ressources, mentors et pratique"
            min_exp, req_hours = 0.0, 8
        elif team_size > 1 or any(
            k in lowered
            for k in ("equipe", "construire", "plateforme", "cofondateur", "collaborateurs")
        ):
            intent = IntentType.BUILD_TEAM
            universe = Universe.PROJECTS
            targets = (EntityKind.PERSON, EntityKind.MENTOR)
            goal = "Constituer une equipe complementaire pour concevoir et livrer un projet"
            team_size = max(team_size, 3)
            min_exp, req_hours = 1.0, 15
        elif any(k in lowered for k in ("communaute", "groupe", "evenement", "hackathon")):
            intent = IntentType.JOIN_COMMUNITY
            universe = Universe.COMMUNITY
            targets = (EntityKind.COMMUNITY, EntityKind.PROJECT)
            goal = "Rejoindre un collectif actif et des evenements collaboratifs"
            min_exp, req_hours = 0.0, 5
        elif any(
            k in lowered
            for k in ("j ai des competences", "mettre en pratique", "rejoindre", "mission")
        ):
            intent = IntentType.JOIN_PROJECT
            universe = Universe.OPPORTUNITIES
            targets = (EntityKind.PROJECT, EntityKind.COMMUNITY)
            goal = "Valoriser ses competences sur un projet ou une mission concrete"
            min_exp, req_hours = 0.0, 12
        else:
            intent = IntentType.FIND_EXPERT
            universe = Universe.SERVICES
            targets = (EntityKind.PERSON, EntityKind.MENTOR, EntityKind.PROJECT)
            goal = "Identifier une expertise ciblee repondant a un besoin precis"
            min_exp, req_hours = 2.0, 10

        questions: list[str] = []
        if not skills:
            questions.append(
                "Aucune competence technique reconnue : "
                "quel domaine ou quelles competences recherchez-vous ?"
            )
        if len(lowered.split()) < 7:
            questions.append(
                "Quel niveau de maturite attendez-vous (initiation, prototype ou production) ?"
            )
        if not any(w in lowered for w in ("heure", "temps", "semaine", "mois", "disponib")):
            questions.append(
                "Quelle disponibilite hebdomadaire et quel horizon temporel privilegiez-vous ?"
            )
        if intent == IntentType.BUILD_TEAM and len(skills) < 3:
            questions.append(
                "Souhaitez-vous inclure un profil Design UI/UX ou produit en plus de la tech ?"
            )

        summary = (
            f"Intention '{intent.value}' dans '{universe.value}' · "
            f"{len(skills)} competence(s) cle(s) identifiee(s)."
        )
        return Need(
            need_id=need_id,
            raw_query=raw_query.strip(),
            primary_goal=goal,
            intent=intent,
            universe=universe,
            target_kinds=targets,
            required_skills=skills,
            team_size=team_size,
            min_experience=min_exp,
            requested_hours_week=req_hours,
            clarification_questions=tuple(questions),
            summary=summary,
        )
