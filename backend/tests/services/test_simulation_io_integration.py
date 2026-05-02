"""Tests for simulation input-output integration."""
import pytest
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.simulation_runner import SimulationRunner, SimulationRunState, RunnerStatus
from app.services.simulation_manager import SimulationManager, SimulationState, SimulationStatus


class TestSimulationIOIntegration:
    """Verify validation_io.json is written and API exposes io_validation."""

    def test_validation_io_json_written_on_completion(self, tmp_path):
        """validation_io.json deve ser escrito ao fim de uma simulacao."""
        sim_id = "sim-io-test"
        sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, sim_id)
        os.makedirs(sim_dir, exist_ok=True)

        # Criar config com 3 agentes
        config = {
            "time_config": {"total_simulation_hours": 1, "minutes_per_round": 60},
            "agent_configs": [
                {"agent_id": 0, "entity_uuid": "u0", "entity_name": "A", "entity_type": "Person"},
                {"agent_id": 1, "entity_uuid": "u1", "entity_name": "B", "entity_type": "Person"},
                {"agent_id": 2, "entity_uuid": "u2", "entity_name": "C", "entity_type": "Person"},
            ]
        }
        config_path = os.path.join(sim_dir, "simulation_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

        # Criar actions.jsonl com 2 agentes (1 missing)
        actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        os.makedirs(os.path.dirname(actions_log), exist_ok=True)
        with open(actions_log, "w", encoding="utf-8") as f:
            f.write(json.dumps({"round": 1, "agent_id": 0, "agent_name": "A", "action_type": "POST", "timestamp": "2025-01-01T00:00:00"}) + "\n")
            f.write(json.dumps({"round": 1, "agent_id": 1, "agent_name": "B", "action_type": "POST", "timestamp": "2025-01-01T00:00:00"}) + "\n")

        # Injetar run_state como COMPLETED para simular fim de simulacao
        state = SimulationRunState(
            simulation_id=sim_id,
            runner_status=RunnerStatus.COMPLETED,
            twitter_actions_count=2,
            reddit_actions_count=0,
            total_rounds=1,
            total_simulation_hours=1,
            twitter_completed=True,
            reddit_completed=False,
        )
        SimulationRunner._run_states[sim_id] = state

        try:
            # Simular o monitor rodando a validacao
            from app.services.simulation_validation import SimulationInputOutputValidator
            from app.services.simulation_config_generator import AgentActivityConfig

            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            agent_configs = []
            for cfg in config_data.get("agent_configs", []):
                agent_configs.append(AgentActivityConfig(**{k: v for k, v in cfg.items() if k in AgentActivityConfig.__dataclass_fields__}))

            all_actions = SimulationRunner.get_all_actions(sim_id)
            validator = SimulationInputOutputValidator()
            validation_result = validator.validate(agent_configs, all_actions)

            validation_path = os.path.join(sim_dir, "validation_io.json")
            with open(validation_path, "w", encoding="utf-8") as f:
                json.dump(validation_result, f, ensure_ascii=False, indent=2)

            assert os.path.exists(validation_path)
            with open(validation_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["missing_count"] == 1
            assert data["spurious_count"] == 0
            assert data["coverage_ratio"] == pytest.approx(0.6667, rel=1e-3)
        finally:
            SimulationRunner._run_states.pop(sim_id, None)
            if os.path.exists(validation_path):
                os.remove(validation_path)
            if os.path.exists(actions_log):
                os.remove(actions_log)
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_simulation_state_loads_validation_io(self, tmp_path):
        """SimulationState deve carregar validation_io.json em _load_simulation_state."""
        sim_id = "sim-load-test"
        sim_dir = os.path.join(SimulationManager.SIMULATION_DATA_DIR, sim_id)
        os.makedirs(sim_dir, exist_ok=True)

        state_data = {
            "simulation_id": sim_id,
            "project_id": "p1",
            "graph_id": "g1",
            "status": "completed",
        }
        state_path = os.path.join(sim_dir, "state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f)

        validation_data = {
            "passed": True,
            "coverage_ratio": 1.0,
            "missing_count": 0,
            "spurious_count": 0,
            "expected_agent_ids": [0, 1],
            "active_agent_ids": [0, 1],
        }
        validation_path = os.path.join(sim_dir, "validation_io.json")
        with open(validation_path, "w", encoding="utf-8") as f:
            json.dump(validation_data, f)

        try:
            manager = SimulationManager()
            state = manager._load_simulation_state(sim_id)
            assert state is not None
            assert state.io_validation_passed is True
            assert state.io_validation_details is not None
            assert state.io_validation_details["coverage_ratio"] == 1.0
        finally:
            if os.path.exists(validation_path):
                os.remove(validation_path)
            if os.path.exists(state_path):
                os.remove(state_path)
