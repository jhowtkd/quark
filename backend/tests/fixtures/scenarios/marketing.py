"""Fixture for the Marketing scenario."""
from .schema import ScenarioFixture, StageExpectation

MARKETING_FIXTURE = ScenarioFixture(
    name="marketing",
    profile="marketing",
    simulation_requirement=(
        "Simular o lancamento de uma campanha de marketing digital para um smartphone "
        "sustentavel, analisando a reacao de consumidores, tech reviewers, concorrentes "
        "e agencias de publicidade nas redes sociais."
    ),
    topic="Lancamento de smartphone sustentavel",
    env_config={
        "chunkSize": 800,
        "chunkOverlap": 150,
        "maxRounds": 8,
        "minutesPerRound": 30,
        "echo_chamber_strength": 0.4,
    },
    expectations=StageExpectation(
        grafo_min_entities=6,
        grafo_min_relations=4,
        grafo_max_unknown_rate=0.25,
        simulation_min_actions=20,
        simulation_min_hours=4,
        report_min_sections=4,
        report_must_have_summary=True,
        report_must_have_conclusions=True,
        report_language_pt_rate=0.90,
    ),
)
