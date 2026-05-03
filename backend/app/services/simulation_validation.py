"""
Validacao input-output de simulacao
Compara agentes previstos no input com agentes ativos no output
"""

import json
import os
from typing import Dict, Any, List

from .simulation_config_generator import AgentActivityConfig
from .simulation_runner import SimulationRunner, AgentAction


class SimulationInputOutputValidator:
    """
    Validador de fidelidade input-output da simulacao

    Garante que todo agente previsto no input apareca no output,
    e que nenhum agente espurio apareca no output.
    """

    def validate(
        self,
        agent_configs: List[AgentActivityConfig],
        all_actions: List[AgentAction],
    ) -> Dict[str, Any]:
        """
        Valida correspondencia entre agentes de input e output.

        Args:
            agent_configs: Configuracoes de agentes do input
            all_actions: Acoes registradas na simulacao

        Returns:
            Dict com metricas de cobertura e discrepancias
        """
        expected_agent_ids = {a.agent_id for a in agent_configs}
        active_agent_ids = {a.agent_id for a in all_actions}

        missing_agent_ids = expected_agent_ids - active_agent_ids
        spurious_agent_ids = active_agent_ids - expected_agent_ids

        missing_count = len(missing_agent_ids)
        spurious_count = len(spurious_agent_ids)

        coverage_ratio = (
            len(active_agent_ids) / len(expected_agent_ids)
            if expected_agent_ids
            else 1.0
        )

        passed = coverage_ratio >= 0.90 and spurious_count == 0

        return {
            "expected_agent_ids": sorted(list(expected_agent_ids)),
            "active_agent_ids": sorted(list(active_agent_ids)),
            "missing_agent_ids": sorted(list(missing_agent_ids)),
            "spurious_agent_ids": sorted(list(spurious_agent_ids)),
            "missing_count": missing_count,
            "spurious_count": spurious_count,
            "coverage_ratio": round(coverage_ratio, 4),
            "passed": passed,
        }

    @staticmethod
    def from_state(simulation_state) -> "SimulationInputOutputValidator":
        """
        Cria validador a partir de um SimulationState.

        Extrai agent_configs de state.config e all_actions de SimulationRunner.
        """
        validator = SimulationInputOutputValidator()

        config = getattr(simulation_state, "config", None)
        agent_configs: List[AgentActivityConfig] = []

        if config is None:
            simulation_id = getattr(simulation_state, "simulation_id", None)
            if simulation_id:
                sim_dir = os.path.join(
                    SimulationRunner.RUN_STATE_DIR, simulation_id
                )
                config_path = os.path.join(sim_dir, "simulation_config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)

        if config:
            raw_configs = (
                config.get("agent_configs", [])
                if isinstance(config, dict)
                else getattr(config, "agent_configs", [])
            )
            for cfg in raw_configs:
                if isinstance(cfg, dict):
                    agent_configs.append(
                        AgentActivityConfig(
                            **{
                                k: v
                                for k, v in cfg.items()
                                if k in AgentActivityConfig.__dataclass_fields__
                            }
                        )
                    )
                else:
                    agent_configs.append(cfg)

        simulation_id = getattr(simulation_state, "simulation_id", None)
        all_actions: List[AgentAction] = []
        if simulation_id:
            all_actions = SimulationRunner.get_all_actions(simulation_id)

        validator._extracted_agent_configs = agent_configs
        validator._extracted_all_actions = all_actions
        return validator
