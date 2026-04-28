"""Tests for graph-build preview cost estimation."""

import math
import sys
from pathlib import Path

import pytest

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

    project = ProjectManager.create_project("Preview Project")
    project.status = ProjectStatus.ONTOLOGY_GENERATED
    project.ontology = {
        "entity_types": [{"name": "Person", "attributes": []}],
        "edge_types": [{"name": "RELATED_TO", "source_targets": [{"source": "Person", "target": "Person"}]}],
    }
    ProjectManager.save_project(project)
    ProjectManager.save_extracted_text(project.project_id, text)
    return project


def test_preview_returns_estimate_and_normalized_settings(monkeypatch, tmp_path):
    """Preview should echo normalized settings and estimated usage before task creation."""
    from app.models.task import TaskManager

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 500)

    task_manager = TaskManager()
    before_tasks = len(task_manager.list_tasks())

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "preview": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["chunk_size"] == 300
    assert data["chunk_overlap"] == 30
    assert data["chunk_count"] >= 1
    assert data["estimated_total_chars"] == 500
    expected_chunks = ["A" * 300, "A" * 230]
    expected_bytes = sum(len(chunk.encode("utf-8")) for chunk in expected_chunks)
    expected_credits = sum(math.ceil(len(chunk.encode("utf-8")) / 350) for chunk in expected_chunks)
    assert data["estimated_total_bytes"] == expected_bytes
    assert data["estimated_credits"] == expected_credits
    assert data["warning_level"] in {"none", "warning"}

    after_tasks = len(task_manager.list_tasks())
    assert after_tasks == before_tasks


def test_preview_warns_for_expensive_build(monkeypatch, tmp_path):
    """Preview should surface a warning level for expensive builds."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 12000)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "preview": True},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["estimated_credits"] >= 25
    assert data["warning_level"] == "warning"


def test_preview_respects_explicit_overrides(monkeypatch, tmp_path):
    """Preview should use explicit request overrides instead of normalized project defaults."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 900)

    response = client.post(
        "/api/graph/build",
        json={
            "project_id": project.project_id,
            "preview": True,
            "chunk_size": 450,
            "chunk_overlap": 15,
        },
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["chunk_size"] == 450
    assert data["chunk_overlap"] == 15
    assert data["chunk_count"] >= 2


def test_preview_does_not_require_zep_api_key(monkeypatch, tmp_path):
    """Preview is a local estimate and should still work without Zep credentials."""
    from app.config import Config

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 900)
    monkeypatch.setattr(Config, "ZEP_API_KEY", None)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "preview": True},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["estimated_credits"] >= 1
