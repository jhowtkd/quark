"""Integrity tests for scenario fixtures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from tests.fixtures.scenarios.loader import list_scenarios, load_scenario
from tests.fixtures.scenarios.schema import ScenarioFixture


def test_all_scenarios_loadable():
    for name in list_scenarios():
        fixture = load_scenario(name)
        assert isinstance(fixture, ScenarioFixture)
        assert fixture.name == name


def test_all_fixtures_have_requirement():
    for name in list_scenarios():
        fixture = load_scenario(name)
        assert fixture.simulation_requirement
        assert len(fixture.simulation_requirement) >= 50


def test_all_fixtures_have_env_config():
    required_keys = {"chunkSize", "chunkOverlap", "maxRounds", "minutesPerRound", "echo_chamber_strength"}
    for name in list_scenarios():
        fixture = load_scenario(name)
        assert required_keys.issubset(fixture.env_config.keys())


def test_all_expectations_have_positive_thresholds():
    for name in list_scenarios():
        fixture = load_scenario(name)
        exp = fixture.expectations
        assert exp.grafo_min_entities > 0
        assert exp.grafo_min_relations > 0
        assert exp.simulation_min_actions > 0
        assert exp.simulation_min_hours > 0
        assert exp.report_min_sections > 0
        assert exp.report_language_pt_rate > 0


def test_unknown_rate_within_valid_range():
    for name in list_scenarios():
        fixture = load_scenario(name)
        rate = fixture.expectations.grafo_max_unknown_rate
        assert 0.0 <= rate <= 1.0
