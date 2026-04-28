"""Tests for rebuild skip behavior."""

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

    project = ProjectManager.create_project("Skip Project")
    project.status = ProjectStatus.GRAPH_COMPLETED
    project.ontology = {
        "entity_types": [{"name": "Person", "attributes": []}],
        "edge_types": [{"name": "RELATED_TO", "source_targets": [{"source": "Person", "target": "Person"}]}],
    }
    ProjectManager.save_project(project)
    ProjectManager.save_extracted_text(project.project_id, text)
    return project


def test_rebuild_skips_when_unchanged(monkeypatch, tmp_path):
    from app.models.project import ProjectManager
    from app.services.text_processor import TextProcessor

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    # Store signatures as if a build already happened
    text = ProjectManager.get_extracted_text(project.project_id)
    project.text_signature = TextProcessor.compute_signature(text)
    import json
    project.ontology_signature = TextProcessor.compute_signature(json.dumps(project.ontology, sort_keys=True))
    ProjectManager.save_project(project)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["skipped"] is True


def test_rebuild_runs_when_text_changed(monkeypatch, tmp_path):
    from app.models.project import ProjectManager
    from app.services.text_processor import TextProcessor

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    # Store old signatures
    project.text_signature = TextProcessor.compute_signature("old text")
    import json
    project.ontology_signature = TextProcessor.compute_signature(json.dumps(project.ontology, sort_keys=True))
    ProjectManager.save_project(project)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "task_id" in payload["data"]  # Normal build creates a task


def test_force_rebuild_bypasses_skip(monkeypatch, tmp_path):
    from app.models.project import ProjectManager
    from app.services.text_processor import TextProcessor

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    # Store matching signatures
    text = ProjectManager.get_extracted_text(project.project_id)
    project.text_signature = TextProcessor.compute_signature(text)
    import json
    project.ontology_signature = TextProcessor.compute_signature(json.dumps(project.ontology, sort_keys=True))
    ProjectManager.save_project(project)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "force": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "task_id" in payload["data"]  # Force always creates a task
