"""Fixture for the Direito (Law) scenario."""
from .schema import ScenarioFixture, StageExpectation

DIREITO_FIXTURE = ScenarioFixture(
    name="direito",
    profile="direito",
    simulation_requirement=(
        "Simular o debate publico sobre uma proposta de reforma do Codigo de Defesa do "
        "Consumidor, incluindo advogados, juizes, associacoes de consumidores, empresas "
        "do varejo e jornalistas especializados."
    ),
    topic="Reforma do Codigo de Defesa do Consumidor",
    env_config={
        "chunkSize": 900,
        "chunkOverlap": 200,
        "maxRounds": 8,
        "minutesPerRound": 30,
        "echo_chamber_strength": 0.35,
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
