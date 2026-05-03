"""Fixture for the Geopolitica scenario."""
from .schema import ScenarioFixture, StageExpectation

GEOPOLITICA_FIXTURE = ScenarioFixture(
    name="geopolitica",
    profile="geopolitica",
    simulation_requirement=(
        "Simular a reacao internacional a uma descoberta de reservas de litio em territorio "
        "disputado na America do Sul, incluindo governos, ONGs ambientais, mineradoras, "
        "analistas geopoliticos e comunidades locais."
    ),
    topic="Descoberta de reservas de litio em territorio disputado",
    env_config={
        "chunkSize": 900,
        "chunkOverlap": 200,
        "maxRounds": 10,
        "minutesPerRound": 30,
        "echo_chamber_strength": 0.45,
    },
    expectations=StageExpectation(
        grafo_min_entities=7,
        grafo_min_relations=5,
        grafo_max_unknown_rate=0.25,
        simulation_min_actions=25,
        simulation_min_hours=5,
        report_min_sections=4,
        report_must_have_summary=True,
        report_must_have_conclusions=True,
        report_language_pt_rate=0.90,
    ),
)
