"""Tests for SimulationInputOutputValidator."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.simulation_validation import SimulationInputOutputValidator
from app.services.simulation_config_generator import AgentActivityConfig
from app.services.simulation_runner import AgentAction


class TestSimulationInputOutputValidator:
    """Verify input-output validator computes coverage, missing, and spurious correctly."""

    def _make_configs(self, count: int) -> list[AgentActivityConfig]:
        return [
            AgentActivityConfig(
                agent_id=i,
                entity_uuid=f"uuid-{i}",
                entity_name=f"Agent {i}",
                entity_type="Person",
            )
            for i in range(count)
        ]

    def _make_actions(self, agent_ids: list[int]) -> list[AgentAction]:
        return [
            AgentAction(
                round_num=1,
                timestamp="2025-01-01T00:00:00",
                platform="twitter",
                agent_id=aid,
                agent_name=f"Agent {aid}",
                action_type="CREATE_POST",
            )
            for aid in agent_ids
        ]

    def test_ten_input_nine_output_one_missing(self):
        """10 agents input, 9 output (1 missing) -> coverage_ratio=0.9, passed=True (threshold >= 0.90)."""
        validator = SimulationInputOutputValidator()
        agent_configs = self._make_configs(10)
        all_actions = self._make_actions(list(range(9)))

        result = validator.validate(agent_configs, all_actions)

        assert result["missing_count"] == 1
        assert result["spurious_count"] == 0
        assert result["coverage_ratio"] == 0.9
        assert result["passed"] is True
        assert result["missing_agent_ids"] == [9]

    def test_ten_input_eleven_output_one_spurious(self):
        """10 agents input, 11 output (1 spurious) -> passed=False, spurious_count=1."""
        validator = SimulationInputOutputValidator()
        agent_configs = self._make_configs(10)
        all_actions = self._make_actions(list(range(11)))

        result = validator.validate(agent_configs, all_actions)

        assert result["missing_count"] == 0
        assert result["spurious_count"] == 1
        assert result["coverage_ratio"] == 1.1
        assert result["passed"] is False
        assert result["spurious_agent_ids"] == [10]

    def test_ten_input_ten_output_perfect(self):
        """10 agents input, 10 output -> passed=True, coverage_ratio=1.0."""
        validator = SimulationInputOutputValidator()
        agent_configs = self._make_configs(10)
        all_actions = self._make_actions(list(range(10)))

        result = validator.validate(agent_configs, all_actions)

        assert result["missing_count"] == 0
        assert result["spurious_count"] == 0
        assert result["coverage_ratio"] == 1.0
        assert result["passed"] is True

    def test_empty_input_empty_output(self):
        """Empty input and output -> coverage_ratio=1.0, passed=True."""
        validator = SimulationInputOutputValidator()
        result = validator.validate([], [])

        assert result["coverage_ratio"] == 1.0
        assert result["passed"] is True

    def test_from_state_returns_validator(self):
        """from_state static method returns a SimulationInputOutputValidator instance."""

        class FakeState:
            simulation_id = "nonexistent_sim_for_test"
            config = None

        validator = SimulationInputOutputValidator.from_state(FakeState())
        assert isinstance(validator, SimulationInputOutputValidator)
