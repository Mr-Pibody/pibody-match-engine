from __future__ import annotations

import re
import unicodedata

SKILL_SYNONYMS: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "python 3.11": "python",
    "fast api": "fastapi",
    "ts": "typescript",
    "js": "javascript",
    "ecmascript": "javascript",
    "react.js": "react",
    "reactjs": "react",
    "next.js": "nextjs",
    "next": "nextjs",
    "node": "nodejs",
    "node.js": "nodejs",
    "postgres": "postgresql",
    "psql": "postgresql",
    "pg": "postgresql",
    "mariadb": "mysql",
    "ds": "data_science",
    "datascience": "data_science",
    "ml": "machine_learning",
    "machine learning": "machine_learning",
    "ia": "machine_learning",
    "ai": "machine_learning",
    "dl": "deep_learning",
    "deep learning": "deep_learning",
    "cv": "computer_vision",
    "vision": "computer_vision",
    "taln": "nlp",
    "natural language processing": "nlp",
    "de": "data_engineering",
    "data engineering": "data_engineering",
    "apache spark": "spark",
    "pyspark": "spark",
    "amazon web services": "aws",
    "cloud aws": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "k8s": "kubernetes",
    "ci/cd": "ci_cd",
    "cicd": "ci_cd",
    "github actions": "ci_cd",
    "architecture": "system_design",
    "system design": "system_design",
    "scrum": "agile",
}


def normalize_skill_token(raw: str) -> str:
    """Normalise une chaine de competence (casse, accents, espaces)."""
    decomposed = unicodedata.normalize("NFKD", raw.strip().lower())
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"\s+", " ", ascii_only).strip()
    return cleaned


def resolve_skill_id(raw: str) -> str:
    """Convertit un libelle brut en identifiant canonique stable."""
    norm = normalize_skill_token(raw)
    if norm in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[norm]
    slug = re.sub(r"[^a-z0-9_+.#]+", "_", norm).strip("_")
    return SKILL_SYNONYMS.get(slug, slug)
