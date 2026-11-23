from __future__ import annotations

from pibody_match.domain.opportunities import Opportunity
from pibody_match.domain.profiles import Profile
from pibody_match.domain.skills import SeniorityLevel
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph


def build_reference_dataset() -> tuple[
    tuple[Profile, ...],
    tuple[Opportunity, ...],
    dict[str, dict[str, float]],
]:
    """Construit le catalogue synthetique de reference (6 profils, 4 opportunites)."""
    tax = SkillTaxonomyGraph()

    profiles = (
        Profile(
            profile_id="prof_01",
            display_name="Synthetique · Profil #01 (Backend IA)",
            headline="Ingenieure Backend Python & Machine Learning",
            seniority=SeniorityLevel.SENIOR,
            skills=(
                tax.build_claim("Python", 0.95, 5.0, verified=True),
                tax.build_claim("FastAPI", 0.90, 3.5, verified=True),
                tax.build_claim("Machine Learning", 0.85, 4.0, verified=True),
                tax.build_claim("PostgreSQL", 0.85, 4.0, verified=False),
                tax.build_claim("Docker", 0.80, 3.0, verified=False),
            ),
            objectives_text=(
                "Concevoir des API Python performantes et deployer des modeles de "
                "machine learning en production pour des produits IA a fort impact."
            ),
            total_experience_years=5.5,
            availability_ratio=1.0,
            public_tags=("track:backend_ai", "remote:hybrid"),
        ),
        Profile(
            profile_id="prof_02",
            display_name="Synthetique · Profil #02 (Cloud SRE)",
            headline="Architecte Cloud AWS & Kubernetes DevOps",
            seniority=SeniorityLevel.EXPERT,
            skills=(
                tax.build_claim("Cloud AWS", 0.95, 6.0, verified=True),
                tax.build_claim("Kubernetes", 0.92, 5.0, verified=True),
                tax.build_claim("Docker", 0.95, 6.0, verified=True),
                tax.build_claim("CI/CD", 0.90, 5.0, verified=True),
                tax.build_claim("Linux", 0.90, 7.0, verified=False),
                tax.build_claim("Python", 0.70, 3.0, verified=False),
            ),
            objectives_text=(
                "Piloter des infrastructures cloud resilientes, automatiser les pipelines "
                "ci/cd et securiser les clusters kubernetes haute disponibilite."
            ),
            total_experience_years=7.0,
            availability_ratio=1.0,
            public_tags=("track:cloud_devops", "remote:full"),
        ),
        Profile(
            profile_id="prof_03",
            display_name="Synthetique · Profil #03 (Full-Stack)",
            headline="Developpeuse Full-Stack TypeScript React & Node.js",
            seniority=SeniorityLevel.CONFIRME,
            skills=(
                tax.build_claim("TypeScript", 0.90, 4.0, verified=True),
                tax.build_claim("React", 0.92, 4.0, verified=True),
                tax.build_claim("Next.js", 0.85, 2.5, verified=True),
                tax.build_claim("Node.js", 0.82, 3.0, verified=False),
                tax.build_claim("PostgreSQL", 0.75, 2.5, verified=False),
            ),
            objectives_text=(
                "Construire des interfaces web react et next.js accessibles connectees "
                "a des architectures node.js robustes et orientees produit."
            ),
            total_experience_years=4.0,
            availability_ratio=1.0,
            public_tags=("track:fullstack", "remote:hybrid"),
        ),
        Profile(
            profile_id="prof_04",
            display_name="Synthetique · Profil #04 (Data NLP)",
            headline="Data Scientist NLP & Data Engineering Spark",
            seniority=SeniorityLevel.SENIOR,
            skills=(
                tax.build_claim("Python", 0.90, 4.5, verified=True),
                tax.build_claim("NLP", 0.92, 4.0, verified=True),
                tax.build_claim("Machine Learning", 0.88, 4.5, verified=True),
                tax.build_claim("Apache Spark", 0.82, 3.0, verified=False),
                tax.build_claim("SQL", 0.88, 4.5, verified=True),
            ),
            objectives_text=(
                "Developper des pipelines data spark et des moteurs de traitement "
                "automatique du langage naturel pour l'aide a la decision."
            ),
            total_experience_years=4.8,
            availability_ratio=0.85,
            public_tags=("track:data_ai", "remote:full"),
        ),
        Profile(
            profile_id="prof_05",
            display_name="Synthetique · Profil #05 (Junior Python)",
            headline="Ingenieure Mobile Flutter & Integration API",
            seniority=SeniorityLevel.CONFIRME,
            skills=(
                tax.build_claim("Flutter", 0.92, 3.5, verified=True),
                tax.build_claim("Dart", 0.90, 3.5, verified=True),
                tax.build_claim("TypeScript", 0.65, 2.0, verified=False),
                tax.build_claim("Firebase", 0.75, 2.5, verified=False),
            ),
            objectives_text=(
                "Concevoir des applications mobiles multiplateformes fluides sous flutter "
                "avec synchronisation temps reel et ergonomie soignee."
            ),
            total_experience_years=3.5,
            availability_ratio=1.0,
            public_tags=("track:mobile", "remote:hybrid"),
        ),
        Profile(
            profile_id="prof_06",
            display_name="Synthetique · Profil #06 (Product & Data)",
            headline="Developpeur Backend Junior Django & SQL",
            seniority=SeniorityLevel.JUNIOR,
            skills=(
                tax.build_claim("Python", 0.72, 1.5, verified=True),
                tax.build_claim("Django", 0.70, 1.0, verified=False),
                tax.build_claim("SQL", 0.68, 1.5, verified=False),
            ),
            objectives_text=(
                "Evoluer sur des projets backend python et api rest au sein d'une "
                "equipe agile orientee qualite logicielle."
            ),
            total_experience_years=1.5,
            availability_ratio=1.0,
            public_tags=("track:backend_ai", "remote:onsite"),
        ),
    )

    opportunities = (
        Opportunity(
            opportunity_id="opp_ai_backend",
            title="Lead Backend Python & IA",
            organization="Pibody Labs",
            description_text="Conception d'API Python FastAPI et deploiement de modeles IA.",
            objectives_text=(
                "Construire un moteur de recommandation explicable en python fastapi "
                "avec integration machine learning et base postgresql."
            ),
            requirements=(
                tax.build_requirement("Python", 0.85, min_years=3.0, weight=1.5, mandatory=True),
                tax.build_requirement("FastAPI", 0.80, min_years=2.0, weight=1.2, mandatory=True),
                tax.build_requirement(
                    "Machine Learning", 0.75, min_years=2.0, weight=1.2, mandatory=False
                ),
                tax.build_requirement(
                    "PostgreSQL", 0.70, min_years=2.0, weight=0.8, mandatory=False
                ),
            ),
            min_total_experience=4.0,
            preferred_seniority=SeniorityLevel.SENIOR,
            capacity=1,
            domain_tags=("ai", "backend"),
        ),
        Opportunity(
            opportunity_id="opp_cloud_sre",
            title="Architecte Cloud AWS & Kubernetes",
            organization="Pibody Cloud",
            description_text="Automatisation cloud aws, conteneurs docker et clusters kubernetes.",
            objectives_text=(
                "Fiabiliser l'infrastructure cloud aws, orchestrer les microservices "
                "kubernetes et industrialiser les pipelines ci/cd."
            ),
            requirements=(
                tax.build_requirement("Cloud AWS", 0.85, min_years=4.0, weight=1.5, mandatory=True),
                tax.build_requirement(
                    "Kubernetes", 0.85, min_years=3.0, weight=1.4, mandatory=True
                ),
                tax.build_requirement("Docker", 0.80, min_years=3.0, weight=1.0, mandatory=False),
                tax.build_requirement("CI/CD", 0.75, min_years=2.0, weight=0.9, mandatory=False),
            ),
            min_total_experience=5.0,
            preferred_seniority=SeniorityLevel.EXPERT,
            capacity=1,
            domain_tags=("cloud", "devops"),
        ),
        Opportunity(
            opportunity_id="opp_fullstack_web",
            title="Ingenieur Full-Stack TypeScript & React",
            organization="Pibody Studio",
            description_text="Developpement plateforme web interactive React, Next.js et Node.js.",
            objectives_text=(
                "Livrer une interface moderne en typescript react et next.js connectee "
                "a des services backend node.js et postgresql."
            ),
            requirements=(
                tax.build_requirement(
                    "TypeScript", 0.80, min_years=2.5, weight=1.4, mandatory=True
                ),
                tax.build_requirement("React", 0.80, min_years=2.5, weight=1.4, mandatory=True),
                tax.build_requirement("Next.js", 0.70, min_years=1.5, weight=1.0, mandatory=False),
                tax.build_requirement("Node.js", 0.70, min_years=2.0, weight=1.0, mandatory=False),
            ),
            min_total_experience=3.0,
            preferred_seniority=SeniorityLevel.CONFIRME,
            capacity=1,
            domain_tags=("web", "frontend"),
        ),
        Opportunity(
            opportunity_id="opp_data_nlp",
            title="Senior Data Scientist NLP & Spark",
            organization="Pibody Intelligence",
            description_text="Modelisation NLP, machine learning et pipelines distribues Spark.",
            objectives_text=(
                "Concevoir des modeles nlp et machine learning sur des volumes massifs "
                "via apache spark, python et sql."
            ),
            requirements=(
                tax.build_requirement("NLP", 0.80, min_years=2.5, weight=1.5, mandatory=True),
                tax.build_requirement(
                    "Machine Learning", 0.80, min_years=3.0, weight=1.3, mandatory=True
                ),
                tax.build_requirement("Python", 0.80, min_years=3.0, weight=1.0, mandatory=False),
                tax.build_requirement(
                    "Apache Spark", 0.70, min_years=1.5, weight=1.0, mandatory=False
                ),
            ),
            min_total_experience=4.0,
            preferred_seniority=SeniorityLevel.SENIOR,
            capacity=1,
            domain_tags=("data", "nlp"),
        ),
    )

    ground_truth: dict[str, dict[str, float]] = {
        "opp_ai_backend": {
            "prof_01": 1.0,
            "prof_04": 0.65,
            "prof_06": 0.45,
            "prof_02": 0.20,
            "prof_03": 0.10,
            "prof_05": 0.0,
        },
        "opp_cloud_sre": {
            "prof_02": 1.0,
            "prof_01": 0.35,
            "prof_04": 0.15,
            "prof_03": 0.10,
            "prof_05": 0.0,
            "prof_06": 0.0,
        },
        "opp_fullstack_web": {
            "prof_03": 1.0,
            "prof_05": 0.35,
            "prof_01": 0.25,
            "prof_06": 0.15,
            "prof_02": 0.10,
            "prof_04": 0.10,
        },
        "opp_data_nlp": {
            "prof_04": 1.0,
            "prof_01": 0.70,
            "prof_06": 0.25,
            "prof_02": 0.15,
            "prof_03": 0.05,
            "prof_05": 0.0,
        },
    }

    return profiles, opportunities, ground_truth
