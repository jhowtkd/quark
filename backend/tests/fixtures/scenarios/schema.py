"""Schema for scenario fixtures and pipeline snapshots."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StageExpectation:
    """Minimum expected results per pipeline stage."""

    # Graph stage
    grafo_min_entities: int
    grafo_min_relations: int
    grafo_max_unknown_rate: float

    # Simulation stage
    simulation_min_actions: int
    simulation_min_hours: int

    # Report stage
    report_min_sections: int
    report_must_have_summary: bool
    report_must_have_conclusions: bool
    report_language_pt_rate: float
    report_must_have_data_provenance: bool = False


@dataclass
class PipelineSnapshot:
    """Expected shape of pipeline outputs for a scenario."""

    graph_shape: Dict = field(default_factory=dict)
    simulation_shape: Dict = field(default_factory=dict)
    report_shape: Dict = field(default_factory=dict)


@dataclass
class ScenarioFixture:
    """Complete fixture for a regression scenario."""

    name: str
    profile: str
    simulation_requirement: str
    topic: str
    raw_text: Optional[str] = None
    env_config: Dict = field(default_factory=dict)
    expectations: StageExpectation = field(default_factory=lambda: StageExpectation(
        grafo_min_entities=0,
        grafo_min_relations=0,
        grafo_max_unknown_rate=1.0,
        simulation_min_actions=0,
        simulation_min_hours=0,
        report_min_sections=0,
        report_must_have_summary=False,
        report_must_have_conclusions=False,
        report_language_pt_rate=0.0,
    ))
    snapshot: Optional[PipelineSnapshot] = None
