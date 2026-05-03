"""Fixture for the Economia (Economy) scenario."""
from .schema import ScenarioFixture, StageExpectation

ECONOMIA_FIXTURE = ScenarioFixture(
    name="economia",
    profile="economia",
    simulation_requirement=(
        "Analisar o impacto de uma elevacao de 2% na taxa Selic sobre o comportamento "
        "de investidores pessoa fisica, fintechs, bancos tradicionais e analistas do "
        "mercado financeiro nas redes sociais."
    ),
    topic="Elevacao da taxa Selic em 2%",
    env_config={
        "chunkSize": 800,
        "chunkOverlap": 150,
        "maxRounds": 10,
        "minutesPerRound": 30,
        "echo_chamber_strength": 0.3,
    },
    expectations=StageExpectation(
        grafo_min_entities=7,
        grafo_min_relations=5,
        grafo_max_unknown_rate=0.20,
        simulation_min_actions=25,
        simulation_min_hours=5,
        report_min_sections=5,
        report_must_have_summary=True,
        report_must_have_conclusions=True,
        report_language_pt_rate=0.90,
        report_must_have_data_provenance=True,
    ),
)
