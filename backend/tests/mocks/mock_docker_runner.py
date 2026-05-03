"""Mock Docker runner simulating simulation_ipc.py behaviour."""

from typing import Any, Dict, List, Optional


class MockDockerRunner:
    """Mock simulation runner returning controlled simulation states."""

    def __init__(
        self,
        states: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.states = states or {}
        self.run_calls: List[Dict[str, Any]] = []

    def run_simulation(
        self,
        simulation_id: str,
        platform: str = "parallel",
        max_rounds: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return a controlled simulation state dict."""
        self.run_calls.append(
            {
                "simulation_id": simulation_id,
                "platform": platform,
                "max_rounds": max_rounds,
                **kwargs,
            }
        )
        default_state = {
            "simulation_id": simulation_id,
            "status": "completed",
            "runner_status": "completed",
            "current_round": 144,
            "total_rounds": 144,
            "simulated_hours": 72,
            "total_simulation_hours": 72,
            "progress_percent": 100.0,
            "twitter_actions_count": 80,
            "reddit_actions_count": 64,
            "total_actions_count": 144,
            "twitter_running": False,
            "reddit_running": False,
            "twitter_completed": True,
            "reddit_completed": True,
            "error": None,
            "started_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T02:00:00",
        }
        return self.states.get(simulation_id, default_state)

    def stop_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Return a stopped simulation state."""
        state = self.run_simulation(simulation_id)
        state["status"] = "stopped"
        state["runner_status"] = "stopped"
        state["twitter_running"] = False
        state["reddit_running"] = False
        return state
