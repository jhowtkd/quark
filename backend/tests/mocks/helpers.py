"""Helpers to wire the pipeline with injected mocks."""

from typing import Any, Dict

from .mock_llm_client import MockLLMClient
from .mock_zep_backend import MockZepBackend
from .mock_docker_runner import MockDockerRunner


def make_scenario_runner(scenario_fixture: Any) -> Dict[str, Any]:
    """Wire the pipeline with injected mocks for a scenario fixture.

    Returns a dict with keys: llm, zep, runner, scenario.
    """
    llm = MockLLMClient()
    zep = MockZepBackend()
    runner = MockDockerRunner()
    return {
        "llm": llm,
        "zep": zep,
        "runner": runner,
        "scenario": scenario_fixture,
    }
