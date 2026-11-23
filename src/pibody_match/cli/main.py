from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from pibody_match.api.server import create_http_server
from pibody_match.datasets.reference import build_reference_dataset
from pibody_match.domain.constraints import MatchConstraints
from pibody_match.evaluation.metrics import evaluate_ranking_suite
from pibody_match.optimizer.gale_shapley import compute_stable_matching
from pibody_match.optimizer.hungarian import optimize_global_assignment
from pibody_match.optimizer.ranking import rank_profiles_for_opportunity
from pibody_match.scoring.weights import ScoreWeights

if TYPE_CHECKING:
    from collections.abc import Sequence

PRESETS: dict[str, ScoreWeights] = {
    "default": ScoreWeights(),
    "tech": ScoreWeights(skills=0.50, objectives=0.15, experience=0.15, requirements=0.20),
    "vision": ScoreWeights(skills=0.25, objectives=0.45, experience=0.15, requirements=0.15),
}


def build_parser() -> argparse.ArgumentParser:
    """Construit l'interface en ligne de commande du moteur."""
    parser = argparse.ArgumentParser(
        prog="pibody-match",
        description="Pibody Match Engine - Moteur d'appariement explicable et d'optimisation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo_p = sub.add_parser("demo", help="Execute une demonstration complete sur le jeu de test")
    demo_p.add_argument("--json", action="store_true", help="Affiche la sortie au format JSON")

    rank_p = sub.add_parser("rank", help="Classe les candidats pour une opportunite donnee")
    rank_p.add_argument("--opportunity", default="opp_ai_backend")
    rank_p.add_argument("--top-k", type=int, default=3)
    rank_p.add_argument("--preset", choices=("default", "tech", "vision"), default="default")
    rank_p.add_argument("--strict", action="store_true")

    opt_p = sub.add_parser("optimize", help="Compare Hongrois et Gale-Shapley")
    opt_p.add_argument("--preset", choices=("default", "tech", "vision"), default="default")

    bench_p = sub.add_parser("benchmark", help="Calcule Precision@K, Recall@K et NDCG@K")
    bench_p.add_argument("--k", type=int, default=2)

    serve_p = sub.add_parser("serve", help="Demarre le Studio Web interactif")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)
    serve_p.add_argument("--db", default="data/pibody_match.db")
    serve_p.add_argument("--demo", action="store_true", help="Pre-remplit avec le jeu d essai")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entree principal de la CLI pibody-match."""
    parser = build_parser()
    args = parser.parse_args(argv)
    profiles, opportunities, ground_truth = build_reference_dataset()

    if args.command == "demo":
        hungarian = optimize_global_assignment(profiles, opportunities)
        gale = compute_stable_matching(profiles, opportunities)
        if args.json:
            payload = {"hungarian": asdict(hungarian), "gale_shapley": asdict(gale)}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(
                f"Hongrois: {len(hungarian.assignments)} affectations | "
                f"score global={hungarian.total_global_score:.4f}"
            )
            print(f"Gale-Shapley: stable={gale.is_stable} | score total={gale.total_score:.4f}")
        return 0

    if args.command == "rank":
        weights = PRESETS[args.preset]
        opp_map = {o.opportunity_id: o for o in opportunities}
        opp = opp_map.get(args.opportunity, opportunities[0])
        constraints = MatchConstraints(strict_mandatory=bool(args.strict))
        ranked = rank_profiles_for_opportunity(
            opp,
            profiles,
            top_k=args.top_k,
            weights=weights,
            constraints=constraints,
        )
        for idx, res in enumerate(ranked, start=1):
            print(f"#{idx} {res.profile_name} ({res.breakdown.total_score * 100:.1f}%)")
        return 0

    if args.command == "optimize":
        weights = PRESETS[args.preset]
        hungarian = optimize_global_assignment(profiles, opportunities, weights=weights)
        gale = compute_stable_matching(profiles, opportunities, weights=weights)
        print(
            f"Hongrois: total={hungarian.total_global_score:.4f} | "
            f"Gale-Shapley: stable={gale.is_stable}"
        )
        return 0

    if args.command == "benchmark":
        opp_map = {o.opportunity_id: o for o in opportunities}
        for opp_id, grades in ground_truth.items():
            ranked = rank_profiles_for_opportunity(opp_map[opp_id], profiles, top_k=len(profiles))
            m = evaluate_ranking_suite([r.profile_id for r in ranked], grades, k=args.k)
            print(
                f"{opp_id}: P@{args.k}={m.precision_at_k:.3f} "
                f"R@{args.k}={m.recall_at_k:.3f} NDCG@{args.k}={m.ndcg_at_k:.3f}"
            )
        return 0

    if args.command == "serve":
        server = create_http_server(
            host=args.host,
            port=args.port,
            db_path=args.db,
            seed_demo=bool(args.demo),
        )
        mode = "MODE DEMO" if args.demo else "MODE PRODUCTION (base vierge)"
        print(f"Pibody Match Studio [{mode}] actif sur http://{args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
