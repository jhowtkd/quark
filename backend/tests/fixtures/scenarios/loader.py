"""Centralized loader for scenario fixtures."""
from typing import List

from .schema import ScenarioFixture
from .saude import SAUDE_FIXTURE
from .marketing import MARKETING_FIXTURE
from .direito import DIREITO_FIXTURE
from .economia import ECONOMIA_FIXTURE
from .geopolitica import GEOPOLITICA_FIXTURE

SCENARIOS: dict[str, ScenarioFixture] = {
    "saude": SAUDE_FIXTURE,
    "marketing": MARKETING_FIXTURE,
    "direito": DIREITO_FIXTURE,
    "economia": ECONOMIA_FIXTURE,
    "geopolitica": GEOPOLITICA_FIXTURE,
}


def load_scenario(name: str) -> ScenarioFixture:
    """Load a scenario fixture by name.

    Raises:
        KeyError: If the scenario name is not registered.
    """
    if name not in SCENARIOS:
        raise KeyError(f"Scenario '{name}' not found. Available: {list_scenarios()}")
    return SCENARIOS[name]


def list_scenarios() -> List[str]:
    """Return the list of available scenario names."""
    return list(SCENARIOS.keys())


__all__ = [
    "SCENARIOS",
    "load_scenario",
    "list_scenarios",
]
