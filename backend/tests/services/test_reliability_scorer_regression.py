"""Regression tests for ReliabilityScorer across all 5 scenario fixtures."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.services.reliability_scorer import ReliabilityScorer, ReliabilityReport
from tests.fixtures.scenarios.loader import SCENARIOS


def _build_ideal_snapshot(scenario_name: str) -> dict:
    """Construct a snapshot dict from the fixture JSON files."""
    fixture = SCENARIOS[scenario_name]
    snapshot_dir = Path(__file__).parent.parent / "fixtures" / "scenarios" / "snapshots" / scenario_name

    graph = _load_json(snapshot_dir / "graph_snapshot.json")
    simulation = _load_json(snapshot_dir / "simulation_snapshot.json")
    report = _load_json(snapshot_dir / "report_snapshot.json")

    # Add markdown content so the scorer can inspect it
    report["markdown_content"] = _ideal_markdown(scenario_name, report)

    return {"graph": graph, "simulation": simulation, "report": report}


def _load_json(path: Path) -> dict:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ideal_markdown(scenario_name: str, report: dict) -> str:
    """Return a plausible markdown body for the ideal snapshot."""
    lines = [
        f"# Relatorio: {scenario_name.title()}",
        "",
        "## Resumo",
        "Este relatorio analisa o cenario simulado.",
        "",
    ]
    for i in range(report.get("section_count", 5)):
        lines.extend([
            f"## Secao {i + 1}",
            "Conteudo detalhado da secao em portugues.",
            "",
        ])
    lines.extend([
        "## Conclusoes",
        "Conclusoes finais do relatorio.",
        "",
    ])
    return "\n".join(lines)


@pytest.fixture
def scorer() -> ReliabilityScorer:
    return ReliabilityScorer()


# ======================================================================
# Happy-path: ideal snapshots
# ======================================================================

@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_passes_beta_gate(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    result = scorer.score_reliability(snapshot)
    assert isinstance(result, ReliabilityReport)
    assert result.passed_beta is True
    assert result.total_score >= ReliabilityScorer.BETA_MIN_TOTAL


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_structural_minimum(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    structural = scorer.score_structural(snapshot)
    assert structural >= ReliabilityScorer.BETA_MIN_PILLAR


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_content_minimum(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    content = scorer.score_content(snapshot)
    assert content >= ReliabilityScorer.BETA_MIN_PILLAR


# ======================================================================
# Failure modes
# ======================================================================

@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_fails_with_empty_report(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    snapshot["report"]["markdown_content"] = ""
    snapshot["report"]["section_count"] = 0
    result = scorer.score_reliability(snapshot)
    assert result.passed_beta is False


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_fails_with_zero_hours(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    snapshot["simulation"]["simulated_hours"] = 0
    result = scorer.score_reliability(snapshot)
    assert result.passed_beta is False


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_fails_with_high_unknown(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    graph = snapshot["graph"]
    # Force unknown rate to 0.50
    graph["unknown_count"] = graph.get("nodes_count", 8) // 2
    result = scorer.score_reliability(snapshot)
    assert result.passed_beta is False


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_fails_with_thinking_process(scorer: ReliabilityScorer, scenario_name: str):
    snapshot = _build_ideal_snapshot(scenario_name)
    snapshot["report"]["markdown_content"] += "\n<think>\nRaciocinio interno do modelo...\n</think>\n"
    content = scorer.score_content(snapshot)
    assert content < ReliabilityScorer.BETA_MIN_PILLAR
