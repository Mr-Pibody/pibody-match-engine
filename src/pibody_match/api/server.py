from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pibody_match.audit.trail import AuditRecord
from pibody_match.datasets.reference import build_reference_dataset
from pibody_match.datasets.universal_catalog import build_universal_catalog
from pibody_match.domain.constraints import HumanDecision, MatchConstraints
from pibody_match.domain.opportunities import Opportunity
from pibody_match.domain.profiles import Profile
from pibody_match.domain.skills import SeniorityLevel
from pibody_match.domain.universal import (
    Capability,
    EntityKind,
    UniversalMatch,
    Universe,
    UserEntity,
)
from pibody_match.evaluation.metrics import evaluate_ranking_suite
from pibody_match.fairness.bias_guard import (
    check_score_invariance_under_anonymization,
    compute_selection_parity,
)
from pibody_match.intent.parser import NeedParser
from pibody_match.nlp.vectorization import TfidfVectorizer
from pibody_match.optimizer.gale_shapley import compute_stable_matching
from pibody_match.optimizer.hungarian import optimize_global_assignment
from pibody_match.optimizer.ranking import rank_profiles_for_opportunity
from pibody_match.optimizer.team_composer import compose_optimal_team
from pibody_match.scoring.complementarity import (
    build_relationship_graph,
    build_skill_pathways,
    evaluate_universal_match,
)
from pibody_match.scoring.weights import DEFAULT_WEIGHTS, ScoreWeights
from pibody_match.storage.sqlite_store import SqliteMatchRepository
from pibody_match.studio.dashboard import render_studio_html
from pibody_match.taxonomy.skill_graph import SkillTaxonomyGraph

STUDIO_DIR = Path(__file__).resolve().parents[3] / "studio"
MATCH_REVEAL_THRESHOLD = 0.58
RECIPROCITY_REVEAL_THRESHOLD = 0.52


class EngineController:
    """Controleur d'etat et de calcul pour Pibody Match Engine."""

    def __init__(self, repo: SqliteMatchRepository, seed_demo: bool = False) -> None:
        self.repo = repo
        self.taxonomy = SkillTaxonomyGraph()
        self.parser = NeedParser(self.taxonomy)
        self.weights = DEFAULT_WEIGHTS
        self.constraints = MatchConstraints()
        self.active_query: str = ""
        self.ground_truth: dict[str, dict[str, float]] = {}

        if seed_demo:
            self.load_reference_sandbox()

    def load_reference_sandbox(self) -> None:
        """Charge un catalogue synthetique de reference uniquement sur demande explicite."""
        profiles, opportunities, ground_truth = build_reference_dataset()
        self.ground_truth = ground_truth
        if not self.repo.list_profiles():
            for prof in profiles:
                self.repo.save_profile(prof)
        if not self.repo.list_opportunities():
            for opp in opportunities:
                self.repo.save_opportunity(opp)
        if not self.repo.list_universal_entities():
            for ent in build_universal_catalog():
                self.repo.save_universal_entity(ent)

    def _build_vectorizer(self, entities: list[UserEntity]) -> TfidfVectorizer:
        vec = TfidfVectorizer()
        corpus = [
            f"{e.name} {e.headline} {e.bio_and_goals} "
            + " ".join(c.canonical_name for c in e.capabilities)
            for e in entities
        ]
        if self.active_query:
            corpus.append(self.active_query)
        if corpus and hasattr(vec, "fit"):
            vec.fit(corpus)
        return vec

    def _ensure_consent(self) -> None:
        consent = self.repo.get_latest_consent()
        if consent is None or not consent.get("accepted"):
            raise ValueError(
                "Consentement de confidentialite requis avant tout enregistrement de donnees."
            )

    def add_entity(self, payload: dict[str, Any]) -> UserEntity:
        self._ensure_consent()
        """Persiste une entite dans SQLite (restera masquee tant qu'il n'y a pas de match)."""
        raw_skills = [s.strip() for s in str(payload.get("skills", "")).split(",") if s.strip()]
        if not raw_skills:
            raise ValueError("Indiquez au moins une competence separee par une virgule.")
        can_teach = bool(payload.get("open_to_mentor", False))
        caps: list[Capability] = []
        for skill in raw_skills:
            sid, cname, fam = self.taxonomy.canonical_info(skill)
            caps.append(
                Capability(
                    skill_id=sid,
                    canonical_name=cname,
                    family=fam,
                    level=0.88,
                    years=float(payload.get("experience_years", 2.0)),
                    can_teach=can_teach,
                )
            )
        eid = f"ent_{len(self.repo.list_universal_entities()) + 1:03d}"
        entity = UserEntity(
            entity_id=eid,
            name=str(payload["name"]).strip(),
            kind=EntityKind(str(payload.get("kind", "personne"))),
            universe=Universe(str(payload.get("universe", Universe.PROJECTS.value))),
            headline=str(payload["headline"]).strip(),
            bio_and_goals=str(payload["bio_and_goals"]).strip(),
            capabilities=tuple(caps),
            experience_years=float(payload.get("experience_years", 2.0)),
            availability_hours_week=int(payload.get("availability_hours_week", 15)),
            open_to_mentor=can_teach,
            open_to_collaborate=True,
        )
        self.repo.save_universal_entity(entity)
        return entity

    def add_profile(self, payload: dict[str, Any]) -> Profile:
        """Valide et enregistre un nouveau profil candidat dans SQLite."""
        raw_skills = str(payload.get("skills", "")).split(",")
        claims = [
            self.taxonomy.build_claim(
                item.strip(),
                proficiency=float(payload.get("default_proficiency", 0.85)),
                years_experience=float(payload.get("total_experience_years", 2.0)),
                verified=True,
            )
            for item in raw_skills
            if item.strip()
        ]
        if not claims:
            raise ValueError("Ajoutez au moins une competence separee par une virgule.")
        pid = f"prof_{len(self.repo.list_profiles()) + 1:02d}"
        prof = Profile(
            profile_id=pid,
            display_name=str(payload["display_name"]).strip(),
            headline=str(payload.get("headline", "Candidat Pibody")).strip(),
            seniority=SeniorityLevel(str(payload.get("seniority", "confirme"))),
            skills=tuple(claims),
            objectives_text=str(payload["objectives_text"]).strip(),
            total_experience_years=float(payload.get("total_experience_years", 2.0)),
            availability_ratio=1.0,
            public_tags=("track:custom",),
        )
        self.repo.save_profile(prof)
        return prof

    def add_opportunity(self, payload: dict[str, Any]) -> Opportunity:
        """Valide et enregistre une nouvelle opportunite dans SQLite."""
        mand = [s.strip() for s in str(payload.get("mandatory_skills", "")).split(",") if s.strip()]
        opt = [s.strip() for s in str(payload.get("optional_skills", "")).split(",") if s.strip()]
        reqs = [
            self.taxonomy.build_requirement(s, 0.80, min_years=2.0, weight=1.4, mandatory=True)
            for s in mand
        ] + [
            self.taxonomy.build_requirement(s, 0.70, min_years=1.0, weight=1.0, mandatory=False)
            for s in opt
        ]
        if not reqs:
            raise ValueError("Indiquez au moins une competence requise.")
        oid = f"opp_{len(self.repo.list_opportunities()) + 1:02d}"
        desc = str(payload["description_text"]).strip()
        opp = Opportunity(
            opportunity_id=oid,
            title=str(payload["title"]).strip(),
            organization=str(payload.get("organization", "Pibody Partner")).strip(),
            description_text=desc,
            objectives_text=str(payload.get("objectives_text", desc)).strip(),
            requirements=tuple(reqs),
            min_total_experience=float(payload.get("min_total_experience", 2.0)),
            preferred_seniority=SeniorityLevel(str(payload.get("preferred_seniority", "confirme"))),
            capacity=max(1, int(payload.get("capacity", 1))),
            domain_tags=("custom",),
        )
        self.repo.save_opportunity(opp)
        return opp

    @staticmethod
    def _apply_privacy_mask(match: UniversalMatch, index: int) -> dict[str, Any]:
        """Revele l'identite uniquement si le match mutuel depasse le seuil de confiance."""
        is_public_resource = match.entity_kind in {
            EntityKind.PROJECT,
            EntityKind.RESOURCE,
            EntityKind.COMMUNITY,
        }
        unlocked = is_public_resource or (
            match.combined_score >= MATCH_REVEAL_THRESHOLD
            and match.reciprocity_score >= RECIPROCITY_REVEAL_THRESHOLD
        )
        payload = asdict(match)
        payload["identity_unlocked"] = unlocked
        if not unlocked:
            alias = f"Profil protege #{index:02d}"
            payload["entity_name"] = alias
            payload["explanation"] = (
                f"{alias} ({match.entity_kind.value}) : score {match.combined_score * 100:.0f}%. "
                "Identite masquee tant que le seuil de match mutuel n'est pas atteint."
            )
        return payload

    def _build_universal_state(self) -> dict[str, Any]:
        entities = self.repo.list_universal_entities()
        if not self.active_query.strip():
            return {
                "active_need": None,
                "stored_entities_count": len(entities),
                "consent": self.repo.get_latest_consent(),
                "unlocked_matches_count": 0,
                "universal_matches": [],
                "team_composition": None,
                "skill_pathways": [],
                "relationship_graph": {"nodes": [], "links": []},
            }

        need = self.parser.parse(self.active_query)
        if not entities:
            return {
                "active_need": asdict(need),
                "stored_entities_count": 0,
                "unlocked_matches_count": 0,
                "universal_matches": [],
                "team_composition": None,
                "skill_pathways": [],
                "relationship_graph": {"nodes": [], "links": []},
            }

        vectorizer = self._build_vectorizer(entities)
        matches = [
            evaluate_universal_match(need, ent, self.taxonomy, vectorizer) for ent in entities
        ]
        matches.sort(key=lambda m: m.combined_score, reverse=True)
        masked_matches = [self._apply_privacy_mask(m, idx + 1) for idx, m in enumerate(matches)]
        unlocked_count = sum(1 for item in masked_matches if item["identity_unlocked"])

        entities_by_id = {e.entity_id: e for e in entities}
        team = compose_optimal_team(need, matches, entities_by_id)
        pathways = build_skill_pathways(need, matches, entities)
        graph = build_relationship_graph(need, matches, entities)

        return {
            "active_need": asdict(need),
            "stored_entities_count": len(entities),
            "consent": self.repo.get_latest_consent(),
            "unlocked_matches_count": unlocked_count,
            "universal_matches": masked_matches,
            "team_composition": asdict(team),
            "skill_pathways": [asdict(p) for p in pathways],
            "relationship_graph": graph,
        }

    def build_snapshot(self) -> dict[str, Any]:
        """Calcule l'etat complet serialisable du moteur."""
        profiles = self.repo.list_profiles()
        opportunities = self.repo.list_opportunities()
        rankings: dict[str, list[dict[str, Any]]] = {}
        metrics: dict[str, dict[str, Any]] = {}

        for opp in opportunities:
            ranked = rank_profiles_for_opportunity(
                opp,
                profiles,
                top_k=len(profiles),
                weights=self.weights,
                constraints=self.constraints,
            )
            rankings[opp.opportunity_id] = [asdict(r) for r in ranked]
            rec_ids = [r.profile_id for r in ranked]
            rel_grades = self.ground_truth.get(opp.opportunity_id, {})
            if rel_grades:
                suite = evaluate_ranking_suite(rec_ids, rel_grades, k=2)
                metrics[opp.opportunity_id] = asdict(suite)
            else:
                metrics[opp.opportunity_id] = {
                    "k": 2,
                    "precision_at_k": 1.0,
                    "recall_at_k": 1.0,
                    "ndcg_at_k": 1.0,
                }

        if profiles and opportunities:
            hungarian = optimize_global_assignment(
                profiles, opportunities, weights=self.weights, constraints=self.constraints
            )
            gale_shapley = compute_stable_matching(
                profiles, opportunities, weights=self.weights, constraints=self.constraints
            )
            cohorts = {
                p.profile_id: next(
                    (t.split(":", 1)[1] for t in p.public_tags if t.startswith("track:")),
                    "general",
                )
                for p in profiles
            }
            selected_ids = [a.profile_id for a in hungarian.assignments]
            invariant = all(
                check_score_invariance_under_anonymization(p, opportunities[0], self.weights)
                for p in profiles
            )
            hungarian_payload = asdict(hungarian)
            gs_payload = asdict(gale_shapley)
            fairness_payload: dict[str, Any] = {
                "anonymization_invariant": invariant,
                "selection_parity": compute_selection_parity(selected_ids, cohorts),
            }
        else:
            hungarian_payload = {"assignments": [], "total_score": 0.0, "average_score": 0.0}
            gs_payload = {"assignments": [], "is_stable": True, "blocking_pairs_count": 0}
            fairness_payload = {"anonymization_invariant": True, "selection_parity": {}}

        snapshot: dict[str, Any] = {
            "weights": asdict(self.weights),
            "constraints": asdict(self.constraints),
            "profiles": [asdict(p) for p in profiles],
            "opportunities": [asdict(o) for o in opportunities],
            "rankings_by_opportunity": rankings,
            "hungarian": hungarian_payload,
            "gale_shapley": gs_payload,
            "evaluation_metrics": metrics,
            "fairness": fairness_payload,
            "audits": [asdict(a) for a in self.repo.list_audits()],
        }
        snapshot.update(self._build_universal_state())
        return snapshot


def create_http_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    db_path: str = ":memory:",
    seed_demo: bool = True,
) -> ThreadingHTTPServer:
    """Instancie le serveur HTTP local du Studio Pibody Match Engine."""
    repo = SqliteMatchRepository(db_path=db_path)
    controller = EngineController(repo, seed_demo=seed_demo)

    class StudioHandler(BaseHTTPRequestHandler):
        def _send_bytes(self, raw: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(raw, "application/json; charset=utf-8", status)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                index_file = STUDIO_DIR / "index.html"
                if index_file.exists():
                    self._send_bytes(index_file.read_bytes(), "text/html; charset=utf-8")
                else:
                    self._send_bytes(
                        render_studio_html().encode("utf-8"), "text/html; charset=utf-8"
                    )
                return
            if self.path == "/css/style.css" and (STUDIO_DIR / "css/style.css").exists():
                self._send_bytes(
                    (STUDIO_DIR / "css/style.css").read_bytes(), "text/css; charset=utf-8"
                )
                return
            if self.path == "/js/app.js" and (STUDIO_DIR / "js/app.js").exists():
                self._send_bytes(
                    (STUDIO_DIR / "js/app.js").read_bytes(),
                    "application/javascript; charset=utf-8",
                )
                return
            if self.path == "/api/state":
                self._send_json(controller.build_snapshot())
                return
            self._send_json({"error": "Endpoint introuvable"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            try:
                if self.path == "/api/consent":
                    accepted = bool(body.get("accepted", False))
                    scope = str(body.get("scope", "storage_and_matching"))
                    ts = datetime.now(UTC).isoformat()
                    controller.repo.record_consent(
                        f"c_{int(datetime.now(UTC).timestamp())}", accepted, scope, ts
                    )
                    self._send_json(controller.build_snapshot())
                    return

                if self.path == "/api/discover":
                    query = str(body.get("query", "")).strip()
                    if not query:
                        raise ValueError("Veuillez decrire votre besoin.")
                    controller.active_query = query
                    self._send_json(controller.build_snapshot())
                    return

                if self.path == "/api/entities":
                    controller.add_entity(body)
                    self._send_json(controller.build_snapshot(), HTTPStatus.CREATED)
                    return

                if self.path == "/api/sandbox/load":
                    controller.load_reference_sandbox()
                    self._send_json(controller.build_snapshot())
                    return

                if self.path == "/api/sandbox/reset":
                    controller.repo.clear_all()
                    controller.active_query = ""
                    controller.ground_truth = {}
                    self._send_json(controller.build_snapshot())
                    return

                if self.path == "/api/evaluate":
                    controller.weights = ScoreWeights(
                        skills=float(body["skills"]),
                        objectives=float(body["objectives"]),
                        experience=float(body["experience"]),
                        requirements=float(body["requirements"]),
                    )
                    controller.constraints = MatchConstraints(
                        strict_mandatory=bool(body.get("strict_mandatory", False))
                    )
                    self._send_json(controller.build_snapshot())
                    return

                if self.path == "/api/profiles":
                    controller.add_profile(body)
                    self._send_json(controller.build_snapshot(), HTTPStatus.CREATED)
                    return

                if self.path == "/api/opportunities":
                    controller.add_opportunity(body)
                    self._send_json(controller.build_snapshot(), HTTPStatus.CREATED)
                    return

                if self.path == "/api/decision":
                    note = str(body.get("reviewer_note", "")).strip()
                    existing = [
                        a
                        for a in controller.repo.list_audits()
                        if a.profile_id == str(body["profile_id"])
                        and a.opportunity_id == str(body["opportunity_id"])
                    ]
                    if (
                        existing
                        and existing[-1].decision.value != str(body["decision"])
                        and not note
                    ):
                        raise ValueError("Justification obligatoire pour modifier une decision.")
                    rec = AuditRecord(
                        audit_id=f"aud_{len(controller.repo.list_audits()) + 1:04d}",
                        match_id=str(body["match_id"]),
                        profile_id=str(body["profile_id"]),
                        opportunity_id=str(body["opportunity_id"]),
                        total_score=float(body["total_score"]),
                        weights_snapshot=asdict(controller.weights),
                        decision=HumanDecision(str(body["decision"])),
                        reviewer_note=note or "Decision initiale validee par le evaluateur.",
                        timestamp_utc=datetime.now(UTC).isoformat(),
                    )
                    controller.repo.save_audit(rec)
                    self._send_json({"audits": [asdict(a) for a in controller.repo.list_audits()]})
                    return
            except (KeyError, ValueError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return

            self._send_json({"error": "Endpoint introuvable"}, HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    return ThreadingHTTPServer((host, port), StudioHandler)
