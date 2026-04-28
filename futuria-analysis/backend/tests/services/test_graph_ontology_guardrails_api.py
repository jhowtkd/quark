"""Tests for ontology guardrails exposed by the graph build API."""

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


def _create_project_with_ontology(text: str, ontology: dict):
    from app.models.project import ProjectManager, ProjectStatus

    project = ProjectManager.create_project("Guardrail Project")
    project.status = ProjectStatus.ONTOLOGY_GENERATED
    project.ontology = ontology
    ProjectManager.save_project(project)
    ProjectManager.save_extracted_text(project.project_id, text)
    return project


def test_preview_returns_ontology_guardrail_warnings(monkeypatch, tmp_path):
    """Preview should surface schema warnings when names are normalized for Zep."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_ontology(
        "A" * 900,
        {
            "entity_types": [{"name": "profissional de rh", "attributes": [{"name": "fullName"}]}],
            "edge_types": [{"name": "compra através de", "source_targets": [{"source": "profissional de rh", "target": "profissional de rh"}]}],
        },
    )

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "preview": True},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["ontology_guardrails"]["can_build"] is True
    assert data["ontology_guardrails"]["errors"] == []
    assert any("profissional de rh" in warning for warning in data["ontology_guardrails"]["warnings"])
    assert any("compra através de" in warning for warning in data["ontology_guardrails"]["warnings"])


def test_build_rejects_ontology_guardrail_errors_before_zep(monkeypatch, tmp_path):
    """Confirmed builds should fail fast when ontology names cannot be safely normalized."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_ontology(
        "A" * 900,
        {
            "entity_types": [{"name": "!!!", "attributes": []}],
            "edge_types": [{"name": "RELATED_TO", "source_targets": [{"source": "!!!", "target": "!!!"}]}],
        },
    )

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "ontology_guardrails" in payload
    assert payload["ontology_guardrails"]["can_build"] is False
    assert payload["ontology_guardrails"]["errors"]
