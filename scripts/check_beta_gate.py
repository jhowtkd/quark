#!/usr/bin/env python3
"""Check beta gate for all scenario snapshots."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.reliability_scorer import ReliabilityScorer
from tests.fixtures.scenarios.loader import SCENARIOS
import json

scorer = ReliabilityScorer()
all_passed = True
for name in SCENARIOS:
    snapshot_dir = backend_dir / "tests" / "fixtures" / "scenarios" / "snapshots" / name
    graph = json.loads((snapshot_dir / "graph_snapshot.json").read_text())
    sim = json.loads((snapshot_dir / "simulation_snapshot.json").read_text())
    report = json.loads((snapshot_dir / "report_snapshot.json").read_text())
    report["markdown_content"] = "Relatorio completo em portugues."
    snapshot = {"graph": graph, "simulation": sim, "report": report}
    result = scorer.score_reliability(snapshot)
    if not result.passed_beta:
        all_passed = False
        failed = [p for p, s in result.pillar_scores.items() if s < scorer.BETA_MIN_PILLAR]
        print(f"FAIL {name}: total={result.total_score:.2f} failed_pillars={failed}")
    else:
        print(f"PASS {name}: total={result.total_score:.2f}")

sys.exit(0 if all_passed else 1)
