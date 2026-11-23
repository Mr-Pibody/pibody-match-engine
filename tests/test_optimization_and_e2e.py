from __future__ import annotations

import json
import threading
import urllib.request
from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from pibody_match.api.server import create_http_server
from pibody_match.audit.trail import AuditRecord, AuditTrail
from pibody_match.cli.main import main as cli_main
from pibody_match.datasets.reference import build_reference_dataset
from pibody_match.domain.constraints import HumanDecision
from pibody_match.evaluation.metrics import evaluate_ranking_suite
from pibody_match.fairness.bias_guard import (
    audit_profile_privacy,
    check_score_invariance_under_anonymization,
    compute_selection_parity,
)
from pibody_match.optimizer.gale_shapley import compute_stable_matching
from pibody_match.optimizer.hungarian import optimize_global_assignment
from pibody_match.optimizer.ranking import evaluate_match, rank_profiles_for_opportunity
from pibody_match.scoring.weights import ScoreWeights
from pibody_match.storage.sqlite_store import SqliteMatchRepository


def test_hungarian_and_gale_shapley_optimality() -> None:
    profiles, opportunities, _ = build_reference_dataset()
    hungarian = optimize_global_assignment(profiles, opportunities)
    assert len(hungarian.assignments) == 4
    assigned_profiles = {a.profile_id for a in hungarian.assignments}
    assert assigned_profiles == {"prof_01", "prof_02", "prof_03", "prof_04"}

    gale = compute_stable_matching(profiles, opportunities)
    assert gale.is_stable is True
    assert len(gale.assignments) == 4
    assert gale.unmatched_profile_ids == ("prof_05", "prof_06")


def test_metrics_fairness_and_audit_trail() -> None:
    profiles, opportunities, ground_truth = build_reference_dataset()
    for opp in opportunities:
        ranked = rank_profiles_for_opportunity(opp, profiles, top_k=len(profiles))
        report = evaluate_ranking_suite(
            [r.profile_id for r in ranked],
            ground_truth[opp.opportunity_id],
            k=2,
        )
        assert report.ndcg_at_k >= 0.95
        assert report.recall_at_k == 1.0

    for prof in profiles:
        assert audit_profile_privacy(prof) == []
        assert check_score_invariance_under_anonymization(prof, opportunities[0])

    parity = compute_selection_parity(["prof_01", "prof_02"], {"prof_01": "a", "prof_02": "b"})
    assert parity == {"a": 1.0, "b": 1.0}

    trail = AuditTrail()
    res = evaluate_match(profiles[0], opportunities[0])
    rec = trail.record_decision(
        res,
        ScoreWeights(0.4, 0.2, 0.2, 0.2),
        decision=HumanDecision.SHORTLISTED,
        reviewer_note="Profil valide",
    )
    assert rec.decision == HumanDecision.SHORTLISTED
    assert "SHORTLISTED" in trail.export_json()


def test_sqlite_repository_roundtrip() -> None:
    profiles, opportunities, _ = build_reference_dataset()
    repo = SqliteMatchRepository(":memory:")
    for p in profiles:
        repo.save_profile(p)
    for o in opportunities:
        repo.save_opportunity(o)

    assert len(repo.list_profiles()) == len(profiles)
    assert len(repo.list_opportunities()) == len(opportunities)

    audit = AuditRecord(
        audit_id="aud_0001",
        match_id="m_1",
        profile_id="prof_01",
        opportunity_id="opp_ai_backend",
        total_score=0.88,
        weights_snapshot={"skills": 0.4, "objectives": 0.2, "experience": 0.2, "requirements": 0.2},
        decision=HumanDecision.SHORTLISTED,
        reviewer_note="Test SQLite",
        timestamp_utc="2026-11-22T16:00:00+00:00",
    )
    repo.save_audit(audit)
    loaded = repo.list_audits()
    assert len(loaded) == 1
    assert loaded[0].decision == HumanDecision.SHORTLISTED
    repo.close()


def test_http_api_and_cli_commands() -> None:
    assert cli_main(["demo", "--json"]) == 0
    assert cli_main(["rank", "--opportunity", "opp_ai_backend", "--top-k", "2"]) == 0
    assert cli_main(["optimize", "--preset", "tech"]) == 0
    assert cli_main(["benchmark", "--k", "2"]) == 0

    server = create_http_server(host="127.0.0.1", port=0, db_path=":memory:")
    port = server.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"{base_url}/") as html_resp:
            assert html_resp.status == 200
            assert b"Pibody Match Engine" in html_resp.read()

        with urllib.request.urlopen(f"{base_url}/api/state") as state_resp:
            state = json.loads(state_resp.read().decode("utf-8"))
            assert state["gale_shapley"]["is_stable"] is True

        req = urllib.request.Request(
            f"{base_url}/api/decision",
            data=json.dumps(
                {
                    "match_id": "prof_01__opp_ai_backend",
                    "profile_id": "prof_01",
                    "opportunity_id": "opp_ai_backend",
                    "total_score": 0.877,
                    "decision": "SHORTLISTED",
                    "reviewer_note": "OK API",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as dec_resp:
            dec_data = json.loads(dec_resp.read().decode("utf-8"))
            assert len(dec_data["audits"]) == 1
    finally:
        server.shutdown()
        server.server_close()


@settings(max_examples=25)
@given(
    w1=st.integers(min_value=1, max_value=10),
    w2=st.integers(min_value=1, max_value=10),
    w3=st.integers(min_value=1, max_value=10),
    w4=st.integers(min_value=1, max_value=10),
    fake_name=st.text(min_size=2, max_size=25).filter(lambda s: bool(s.strip())),
)
def test_property_score_bounds_and_anonymization_invariance(
    w1: int,
    w2: int,
    w3: int,
    w4: int,
    fake_name: str,
) -> None:
    total_w = float(w1 + w2 + w3 + w4)
    weights = ScoreWeights(
        skills=w1 / total_w,
        objectives=w2 / total_w,
        experience=w3 / total_w,
        requirements=w4 / total_w,
    )
    profiles, opportunities, _ = build_reference_dataset()
    prof = profiles[0]
    opp = opportunities[0]

    res = evaluate_match(prof, opp, weights=weights)
    assert 0.0 <= res.breakdown.total_score <= 1.0

    renamed = replace(prof, display_name=fake_name, profile_id="anon_x")
    res_anon = evaluate_match(renamed, opp, weights=weights)
    assert res.breakdown.total_score == res_anon.breakdown.total_score
