"""Fixture for the Saude (Health) scenario."""
from .schema import ScenarioFixture, StageExpectation

SAUDE_FIXTURE = ScenarioFixture(
    name="saude",
    profile="saude",
    simulation_requirement=(
        "Simular a reacao da comunidade medica e do publico geral a aprovacao de um "
        "novo medicamento para diabetes tipo 2 no Brasil, incluindo endocrinologistas, "
        "pacientes, influenciadores de saude e laboratorios farmaceuticos."
    ),
    topic="Aprovacao de novo medicamento para diabetes tipo 2",
    env_config={
        "chunkSize": 800,
        "chunkOverlap": 150,
        "maxRounds": 8,
        "minutesPerRound": 30,
        "echo_chamber_strength": 0.3,
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
