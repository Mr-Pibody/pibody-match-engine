from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillNode:
    """Noeud de la taxonomie hierarchique des competences."""

    skill_id: str
    canonical_name: str
    family: str
    parent_id: str | None = None
    description: str = ""


DEFAULT_SKILL_CATALOG: tuple[SkillNode, ...] = (
    # Famille Backend & Langages
    SkillNode("python", "Python", "backend", None, "Langage generaliste backend et data"),
    SkillNode("fastapi", "FastAPI", "backend", "python", "Framework API asynchrone Python"),
    SkillNode("django", "Django", "backend", "python", "Framework web full-stack Python"),
    SkillNode("flask", "Flask", "backend", "python", "Micro-framework web Python"),
    SkillNode("typescript", "TypeScript", "frontend", None, "JavaScript type statiquement"),
    SkillNode("javascript", "JavaScript", "frontend", None, "Langage web client et serveur"),
    SkillNode("react", "React", "frontend", "typescript", "Bibliotheque UI composants"),
    SkillNode("nextjs", "Next.js", "frontend", "react", "Framework React full-stack"),
    SkillNode("nodejs", "Node.js", "backend", "typescript", "Runtime serveur JavaScript/TS"),
    SkillNode("dart", "Dart", "mobile", None, "Langage client multiplateforme"),
    SkillNode("flutter", "Flutter", "mobile", "dart", "SDK UI natif multiplateforme"),
    SkillNode("go", "Go", "backend", None, "Langage systeme et microservices"),
    SkillNode("java", "Java", "backend", None, "Langage entreprise JVM"),
    # Famille Bases de donnees
    SkillNode("sql", "SQL", "database", None, "Requetage relationnel standard"),
    SkillNode("postgresql", "PostgreSQL", "database", "sql", "SGBD relationnel avance"),
    SkillNode("mysql", "MySQL", "database", "sql", "SGBD relationnel web"),
    SkillNode("redis", "Redis", "database", None, "Store cle-valeur en memoire"),
    # Famille Data & Intelligence Artificielle
    SkillNode("data_science", "Data Science", "data_ai", None, "Analyse et modelisation"),
    SkillNode("pandas", "Pandas", "data_ai", "data_science", "Manipulation tabulaire Python"),
    SkillNode("machine_learning", "Machine Learning", "data_ai", "data_science", "Apprentissage"),
    SkillNode("deep_learning", "Deep Learning", "data_ai", "machine_learning", "Reseaux profonds"),
    SkillNode("computer_vision", "Computer Vision", "data_ai", "deep_learning", "Vision IA"),
    SkillNode("nlp", "NLP", "data_ai", "machine_learning", "Traitement automatique du langage"),
    SkillNode("data_engineering", "Data Engineering", "data_ai", None, "Pipelines data"),
    SkillNode("spark", "Apache Spark", "data_ai", "data_engineering", "Calcul distribue massif"),
    # Famille Cloud & DevOps
    SkillNode("cloud", "Cloud Computing", "cloud_devops", None, "Architectures cloud"),
    SkillNode("aws", "Cloud AWS", "cloud_devops", "cloud", "Amazon Web Services"),
    SkillNode("gcp", "Google Cloud", "cloud_devops", "cloud", "Google Cloud Platform"),
    SkillNode("azure", "Microsoft Azure", "cloud_devops", "cloud", "Cloud Microsoft"),
    SkillNode("devops", "DevOps", "cloud_devops", None, "Automatisation et livraison continue"),
    SkillNode("docker", "Docker", "cloud_devops", "devops", "Conteneurisation applicative"),
    SkillNode("kubernetes", "Kubernetes", "cloud_devops", "docker", "Orchestration de conteneurs"),
    SkillNode("ci_cd", "CI/CD", "cloud_devops", "devops", "Integration et deploiement continus"),
    SkillNode("linux", "Linux", "cloud_devops", "devops", "Administration systeme Linux"),
    # Famille Ingenierie & Transversal
    SkillNode("system_design", "System Design", "architecture", None, "Architecture distribuee"),
    SkillNode("communication", "Communication", "soft_skills", None, "Communication technique"),
    SkillNode("agile", "Agile / Scrum", "soft_skills", None, "Gestion de projet agile"),
    SkillNode("leadership", "Leadership", "soft_skills", None, "Encadrement technique"),
)
