"""Tests for agent evolution integration with simulation runner."""
import pytest
from app.services.simulation_runner import SimulationRunState, RunnerStatus


def test_simulation_run_state_to_detail_dict_includes_agent_evolution():
    state = SimulationRunState(
        simulation_id="test-sim-1",
        runner_status=RunnerStatus.IDLE,
        agent_evolution_enabled=True,
        agent_evolution_preset="stable",
        agent_evolution={"averages": {"fatigue": 0.1}},
    )
    detail = state.to_detail_dict()
    assert "agent_evolution" in detail
    assert detail["agent_evolution_enabled"] is True
    assert detail["agent_evolution_preset"] == "stable"


def test_simulation_run_state_empty_evolution_is_well_shaped():
    state = SimulationRunState(simulation_id="test-sim-2")
    detail = state.to_detail_dict()
    assert "agent_evolution" in detail
    assert detail["agent_evolution"] == {}
    assert detail["agent_evolution_enabled"] is False
    assert detail["agent_evolution_preset"] is None


def test_evolution_summary_includes_averages_and_top_changed_agents():
    from app.services.agent_evolution import (
        EvolutionService,
        EvolutionPolicy,
        summarize_evolution,
    )

    actions = [
        {
            "round_num": 1,
            "agent_id": 1,
            "agent_name": "Alice",
            "platform": "twitter",
            "action_type": "REPOST",
            "success": True,
            "timestamp": "2026-05-07T10:00:00",
        },
        {
            "round_num": 1,
            "agent_id": 2,
            "agent_name": "Bob",
            "platform": "reddit",
            "action_type": "QUOTE_POST",
            "success": True,
            "timestamp": "2026-05-07T10:01:00",
        },
    ]

    result = EvolutionService(policy=EvolutionPolicy.stable()).advance_round({}, actions, round_num=1)
    summary = summarize_evolution(result)
    assert "averages" in summary
    assert "top_changed_agents" in summary
    assert len(summary["top_changed_agents"]) <= 2
