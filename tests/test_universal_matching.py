from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

import pytest

from pibody_match.api.server import create_http_server
from pibody_match.datasets.universal_catalog import build_universal_catalog
from pibody_match.domain.opportunities import Opportunity
from pibody_match.domain.profiles import Profile
from pibody_match.domain.skills import SeniorityLevel
from pibody_match.intent.parser import NeedParser
from pibody_match.nlp.vectorization import TfidfVectorizer
from pibody_match.optimizer.gale_shapley import compute_stable_matching
from pibody_match.optimizer.hungarian import optimize_global_assignment
from pibody_match.optimizer.team_composer import compose_optimal_team
from pibody_match.scoring.complementarity import evaluate_universal_match
from pibody_match.storage.sqlite_store import SqliteMatchRepository
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

if TYPE_CHECKING:
    from pathlib import Path


def test_need_parser_team_and_complementarity() -> None:
    taxonomy = SkillTaxonomyGraph()
    parser = NeedParser(taxonomy)
    need = parser.parse(
        "Je cherche trois personnes complementaires pour construire une plateforme "
        "educative en Python, React et Docker"
    )
    assert need.team_size == 3
    assert set(need.required_skills) >= {"Python", "React", "Docker"}

    catalog = build_universal_catalog()
    vec = TfidfVectorizer()
    vec.fit([f"{e.headline} {e.bio_and_goals}" for e in catalog] + [need.raw_query])
    matches = [evaluate_universal_match(need, e, taxonomy, vec) for e in catalog]
    matches.sort(key=lambda m: m.combined_score, reverse=True)

    team = compose_optimal_team(need, matches, {e.entity_id: e for e in catalog})
    assert len(team.members) == 3
    assert team.collective_coverage >= 0.66


def test_hungarian_and_gale_shapley_stability() -> None:
    taxonomy = SkillTaxonomyGraph()
    p1 = Profile(
        profile_id="p1",
        display_name="Candidat A",
        headline="Polyvalent",
        seniority=SeniorityLevel.SENIOR,
        skills=(taxonomy.build_claim("Python", 0.95, 5.0, True),),
        objectives_text="Projet IA",
        total_experience_years=5.0,
    )
    p2 = Profile(
        profile_id="p2",
        display_name="Candidat B",
        headline="Specialiste",
        seniority=SeniorityLevel.CONFIRME,
        skills=(taxonomy.build_claim("Python", 0.70, 2.0, True),),
        objectives_text="Projet IA",
        total_experience_years=2.0,
    )
    o1 = Opportunity(
        opportunity_id="o1",
        title="Mission Alpha",
        organization="Org",
        description_text="Mission IA",
        objectives_text="Projet IA",
        requirements=(taxonomy.build_requirement("Python", 0.80, 3.0, 1.5, True),),
        min_total_experience=3.0,
        preferred_seniority=SeniorityLevel.SENIOR,
        capacity=1,
    )
    o2 = Opportunity(
        opportunity_id="o2",
        title="Mission Beta",
        organization="Org",
        description_text="Mission Python",
        objectives_text="Projet IA",
        requirements=(taxonomy.build_requirement("Python", 0.60, 1.0, 1.0, False),),
        min_total_experience=1.0,
        preferred_seniority=SeniorityLevel.CONFIRME,
        capacity=1,
    )

    hungarian = optimize_global_assignment([p1, p2], [o1, o2])
    gale_shapley = compute_stable_matching([p1, p2], [o1, o2])
    assert gale_shapley.is_stable is True
    assert len(hungarian.assignments) == len(gale_shapley.assignments) == 2


def test_privacy_progressive_disclosure_and_audit_note_enforcement() -> None:
    server = create_http_server(host="127.0.0.1", port=0, seed_demo=False)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    try:
        state = json.loads(urllib.request.urlopen(f"{base}/api/state").read().decode("utf-8"))
        assert state["stored_entities_count"] == 0
        assert state["active_need"] is None

        # Verification blocage sans consentement prealable (RGPD)
        blocked_req = urllib.request.Request(
            f"{base}/api/entities",
            data=json.dumps({"name": "Test", "skills": "Python"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(blocked_req)
            raise AssertionError("L'enregistrement sans consentement aurait du echouer")
        except urllib.error.HTTPError as consent_err:
            assert consent_err.code == 400

        # Validation explicite du consentement
        consent_req = urllib.request.Request(
            f"{base}/api/consent",
            data=json.dumps({"accepted": True, "scope": "storage_and_matching"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(consent_req) as c_resp:
            c_state = json.loads(c_resp.read().decode("utf-8"))
            assert c_state["consent"]["accepted"] is True

        for name, skills, bio in [
            (
                "Test · Mentor Alpha",
                "Python, Machine Learning, NLP",
                "Mentorat et collaboration sur des projets Python, Machine Learning et NLP",
            ),
            (
                "Test · Profil Beta",
                "React, TypeScript",
                "Developpement frontend web et interfaces utilisateurs",
            ),
        ]:
            req = urllib.request.Request(
                f"{base}/api/entities",
                data=json.dumps(
                    {
                        "name": name,
                        "kind": "mentor",
                        "universe": "Mentorat & Accompagnement",
                        "headline": f"Mentor {skills}",
                        "skills": skills,
                        "experience_years": 6,
                        "availability_hours_week": 20,
                        "open_to_mentor": True,
                        "bio_and_goals": bio,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req)

        disc_req = urllib.request.Request(
            f"{base}/api/discover",
            data=json.dumps(
                {"query": "Je souhaite apprendre Python, Machine Learning et NLP avec un mentor"}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        discovered = json.loads(urllib.request.urlopen(disc_req).read().decode("utf-8"))
        assert discovered["stored_entities_count"] == 2
        names = [m["entity_name"] for m in discovered["universal_matches"]]
        assert "Test · Mentor Alpha" in names
        assert "Test · Profil Beta" not in names
        assert any(n.startswith("Profil protege #") for n in names)

        first_dec = urllib.request.Request(
            f"{base}/api/decision",
            data=json.dumps(
                {
                    "match_id": "m1",
                    "profile_id": "prof_01",
                    "opportunity_id": "opp_01",
                    "total_score": 0.85,
                    "decision": "SHORTLISTED",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(first_dec)

        override_without_note = urllib.request.Request(
            f"{base}/api/decision",
            data=json.dumps(
                {
                    "match_id": "m1",
                    "profile_id": "prof_01",
                    "opportunity_id": "opp_01",
                    "total_score": 0.85,
                    "decision": "REJECTED",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(override_without_note)
        assert err.value.code == 400
    finally:
        server.shutdown()


def test_sqlite_universal_entities_roundtrip(tmp_path: Path) -> None:
    repo = SqliteMatchRepository(tmp_path / "vault.db")
    sample = build_universal_catalog()[:2]
    for ent in sample:
        repo.save_universal_entity(ent)
    loaded = repo.list_universal_entities()
    assert len(loaded) == 2
    assert {e.name for e in loaded} == {e.name for e in sample}
    repo.close()

