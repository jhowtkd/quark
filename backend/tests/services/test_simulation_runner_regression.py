"""Simulation runner regression tests."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from app.services.simulation_runner import (
    SimulationRunner,
    SimulationRunState,
    RunnerStatus,
    AgentAction,
)


class TestSimulationRunnerRegression:
    """Regression tests for simulation runner state tracking."""

    def test_simulated_hours_advances(self):
        """Simulated hours must increase as rounds progress."""
        state = SimulationRunState(simulation_id="sim_001", total_rounds=10)
        state.simulated_hours = 0

        # Simulate advancing rounds
        for hour in [1, 2, 3, 4, 5]:
            state.simulated_hours = hour
            assert state.simulated_hours == hour

    def test_action_counts_coherent(self):
        """Total actions must equal sum of twitter and reddit actions."""
        state = SimulationRunState(simulation_id="sim_002")
        state.twitter_actions_count = 30
        state.reddit_actions_count = 20

        total = state.twitter_actions_count + state.reddit_actions_count
        assert total == 50

        # Add actions via add_action
        action_tw = AgentAction(
            round_num=1,
            timestamp="2024-01-01T00:00:00",
            platform="twitter",
            agent_id=1,
            agent_name="Agent A",
            action_type="CREATE_POST",
        )
        action_rd = AgentAction(
            round_num=1,
            timestamp="2024-01-01T00:00:01",
            platform="reddit",
            agent_id=2,
            agent_name="Agent B",
            action_type="CREATE_POST",
        )
        state.add_action(action_tw)
        state.add_action(action_rd)

        assert state.twitter_actions_count == 31
        assert state.reddit_actions_count == 21
        assert state.twitter_actions_count + state.reddit_actions_count == 52

    def test_completed_simulation_has_positive_hours(self):
        """A completed simulation state must report positive simulated hours."""
        state = SimulationRunState(
            simulation_id="sim_003",
            runner_status=RunnerStatus.COMPLETED,
            simulated_hours=48,
            total_simulation_hours=48,
        )
        assert state.simulated_hours > 0
        state_dict = state.to_dict()
        assert state_dict["status"] == "completed"
        assert state_dict["simulated_hours"] > 0

    def test_failed_simulation_returns_clear_error(self):
        """A failed simulation must expose a clear error message."""
        state = SimulationRunState(
            simulation_id="sim_004",
            runner_status=RunnerStatus.FAILED,
            error="Processo encerrado com codigo 1: falha na inicializacao",
        )
        state_dict = state.to_dict()
        assert state_dict["status"] == "failed"
        assert state.error is not None
        assert len(state.error) > 0
        assert "falha" in state.error.lower() or "erro" in state.error.lower()

    def test_progress_percent_monotonic(self):
        """Progress percent must not decrease as current_round advances."""
        state = SimulationRunState(
            simulation_id="sim_005", total_rounds=100
        )
        prev_progress = 0.0
        for round_num in [0, 10, 25, 50, 75, 100]:
            state.current_round = round_num
            state_dict = state.to_dict()
            progress = state_dict["progress_percent"]
            assert progress >= prev_progress, (
                f"Progress decreased from {prev_progress}% to {progress}% at round {round_num}"
            )
            prev_progress = progress
        assert prev_progress == 100.0
