"""Tests for preview/build safety and non-mutation guarantees."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _make_app(monkeypatch, tmp_path):
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app
    from app.config import Config
    from app.models.project import ProjectManager

    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(upload_root))
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(upload_root / "projects"))

    return create_app()


def _create_project_with_text(text: str):
    from app.models.project import ProjectManager, ProjectStatus

    project = ProjectManager.create_project("Safety Project")
    project.status = ProjectStatus.ONTOLOGY_GENERATED
    project.ontology = {
        "entity_types": [{"name": "Person", "attributes": []}],
        "edge_types": [{"name": "RELATED_TO", "source_targets": [{"source": "Person", "target": "Person"}]}],
    }
    ProjectManager.save_project(project)
    ProjectManager.save_extracted_text(project.project_id, text)
    return project


def test_preview_does_not_mutate_project_state(monkeypatch, tmp_path):
    """Preview must not create graph/task state or advance the project lifecycle."""
    from app.models.project import ProjectManager

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "preview": True},
    )

    assert response.status_code == 200

    reloaded = ProjectManager.get_project(project.project_id)
    assert reloaded is not None
    assert reloaded.status.value == "ontology_generated"
    assert reloaded.graph_id is None
    assert reloaded.graph_build_task_id is None
    assert reloaded.ontology == project.ontology


def test_build_accepts_chunk_overrides_and_creates_task(monkeypatch, tmp_path):
    """Confirmed builds should still create the existing async task flow."""
    from app.models.project import ProjectManager

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    response = client.post(
        "/api/graph/build",
        json={
            "project_id": project.project_id,
            "chunk_size": 420,
            "chunk_overlap": 12,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["task_id"]

    reloaded = ProjectManager.get_project(project.project_id)
    assert reloaded is not None
    assert reloaded.status.value == "graph_building"
    assert reloaded.graph_build_task_id == payload["data"]["task_id"]
    assert reloaded.chunk_size == 420
    assert reloaded.chunk_overlap == 12
