import json

from app.services.simulation_manager import SimulationManager


def _write_state(base_dir, simulation_id: str, project_id: str, graph_id: str) -> None:
    sim_dir = base_dir / simulation_id
    sim_dir.mkdir(parents=True)
    (sim_dir / "state.json").write_text(
        json.dumps(
            {
                "simulation_id": simulation_id,
                "project_id": project_id,
                "graph_id": graph_id,
                "status": "paused",
                "enable_twitter": True,
                "enable_reddit": True,
                "entities_count": 0,
                "profiles_count": 0,
                "entity_types": [],
                "config_generated": False,
                "config_reasoning": "",
                "current_round": 0,
                "twitter_status": "not_started",
                "reddit_status": "not_started",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "error": None,
            }
        ),
        encoding="utf-8",
    )


def test_clear_project_graph_references_only_clears_matching_project(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path))
    _write_state(tmp_path, "sim_a", "proj_target", "graph_target")
    _write_state(tmp_path, "sim_b", "proj_other", "graph_other")

    manager = SimulationManager()
    manager.clear_project_graph_references("proj_target")

    sim_a = json.loads((tmp_path / "sim_a" / "state.json").read_text(encoding="utf-8"))
    sim_b = json.loads((tmp_path / "sim_b" / "state.json").read_text(encoding="utf-8"))

    assert sim_a["graph_id"] == ""
    assert sim_b["graph_id"] == "graph_other"
