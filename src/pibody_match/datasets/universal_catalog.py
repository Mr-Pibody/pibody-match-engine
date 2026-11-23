from __future__ import annotations

from pibody_match.domain.universal import Capability, EntityKind, Universe, UserEntity
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph


def build_universal_catalog() -> list[UserEntity]:
    """Construit le catalogue multi-univers de Pibody Match Engine."""
    tax = SkillTaxonomyGraph()

    def cap(name: str, level: float, years: float, teach: bool = False) -> Capability:
        sid, cname, fam = tax.canonical_info(name)
        return Capability(
            skill_id=sid,
            canonical_name=cname,
            family=fam,
            level=level,
            years=years,
            can_teach=teach,
        )

    return [
        UserEntity(
            entity_id="ent_lucas",
            name="Synthetique · Profil #01 (Backend)",
            kind=EntityKind.PERSON,
            universe=Universe.PROJECTS,
            headline="Developpeur Backend Python & FastAPI",
            bio_and_goals="4 ans d'experience API et SQL, souhaite batir des projets IA utiles.",
            capabilities=(
                cap("Python", 0.92, 4.0),
                cap("FastAPI", 0.90, 3.0),
                cap("PostgreSQL", 0.85, 3.5),
            ),
            experience_years=4.0,
            availability_hours_week=20,
            open_to_mentor=False,
        ),
        UserEntity(
            entity_id="ent_amina",
            name="Synthetique · Mentor #02 (IA & NLP)",
            kind=EntityKind.MENTOR,
            universe=Universe.MENTORSHIP,
            headline="Ingenieure IA & Mentore Machine Learning",
            bio_and_goals="Accompagne les apprenants et equipes IA en Python, NLP et statistiques.",
            capabilities=(
                cap("Python", 0.95, 5.0, True),
                cap("Machine Learning", 0.92, 4.0, True),
                cap("NLP", 0.88, 3.5, True),
            ),
            experience_years=5.0,
            availability_hours_week=12,
            open_to_mentor=True,
        ),
        UserEntity(
            entity_id="ent_koffi",
            name="Synthetique · Profil #03 (Design & Produit)",
            kind=EntityKind.PERSON,
            universe=Universe.PROJECTS,
            headline="Designer Produit & Developpeur Frontend React",
            bio_and_goals="Interfaces modernes, UX/UI et applications web et mobiles intuitives.",
            capabilities=(
                cap("React", 0.92, 4.0),
                cap("TypeScript", 0.88, 3.5),
                cap("UI/UX Design", 0.90, 4.0, True),
            ),
            experience_years=4.0,
            availability_hours_week=18,
            open_to_mentor=True,
        ),
        UserEntity(
            entity_id="ent_nadia",
            name="Synthetique · Mentor #04 (Cybersecurite)",
            kind=EntityKind.MENTOR,
            universe=Universe.SERVICES,
            headline="Experte Cybersecurite, Cloud & DevSecOps",
            bio_and_goals="Securisation d'applications, Docker et mentorat technique cloud.",
            capabilities=(
                cap("Cybersecurity", 0.95, 5.0, True),
                cap("Docker", 0.90, 4.0, True),
                cap("Python", 0.82, 3.0),
            ),
            experience_years=5.0,
            availability_hours_week=15,
            open_to_mentor=True,
        ),
        UserEntity(
            entity_id="ent_proj_edu",
            name="Projet EduPulse IA",
            kind=EntityKind.PROJECT,
            universe=Universe.PROJECTS,
            headline="Plateforme educative adaptative propulsee par l'IA",
            bio_and_goals="Recherche contributeurs Python, React et UX pour l'education.",
            capabilities=(
                cap("Python", 0.80, 2.0),
                cap("React", 0.80, 2.0),
                cap("Machine Learning", 0.80, 2.0),
            ),
            experience_years=2.0,
            availability_hours_week=15,
        ),
        UserEntity(
            entity_id="ent_proj_sec",
            name="Initiative CyberShield Africa",
            kind=EntityKind.PROJECT,
            universe=Universe.OPPORTUNITIES,
            headline="Programme ouvert de securisation d'applications publiques",
            bio_and_goals="Accueille des profils cybersecurite et backend pour des audits.",
            capabilities=(
                cap("Cybersecurity", 0.85, 2.0),
                cap("Docker", 0.80, 2.0),
                cap("Python", 0.75, 1.0),
            ),
            experience_years=2.0,
            availability_hours_week=12,
        ),
        UserEntity(
            entity_id="ent_res_ia",
            name="Parcours Pratique IA & Python",
            kind=EntityKind.RESOURCE,
            universe=Universe.LEARNING,
            headline="Programme guide avec mentorat hebdomadaire et projets reels",
            bio_and_goals="Apprendre Python, FastAPI et Machine Learning pas a pas.",
            capabilities=(
                cap("Python", 0.90, 3.0, True),
                cap("Machine Learning", 0.88, 3.0, True),
                cap("FastAPI", 0.85, 2.0, True),
            ),
            experience_years=3.0,
            availability_hours_week=10,
            open_to_mentor=True,
        ),
        UserEntity(
            entity_id="ent_comm_tech",
            name="Communaute Tech Builders Afrique",
            kind=EntityKind.COMMUNITY,
            universe=Universe.COMMUNITY,
            headline="Collectif de createurs IA, Web, Design et Cybersecurite",
            bio_and_goals="Groupes d'entraide, hackathons et projets collaboratifs.",
            capabilities=(
                cap("Python", 0.85, 3.0, True),
                cap("React", 0.85, 3.0, True),
                cap("Cybersecurity", 0.85, 3.0, True),
            ),
            experience_years=3.0,
            availability_hours_week=10,
            open_to_mentor=True,
        ),
    ]
