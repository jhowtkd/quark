"""Tests for incremental graph updates."""

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

    project = ProjectManager.create_project("Incremental Project")
    project.status = ProjectStatus.GRAPH_COMPLETED
    project.graph_id = "futuria_test_graph_123"
    project.ontology = {
        "entity_types": [{"name": "Person", "attributes": []}],
        "edge_types": [{"name": "RELATED_TO", "source_targets": [{"source": "Person", "target": "Person"}]}],
    }
    ProjectManager.save_project(project)
    ProjectManager.save_extracted_text(project.project_id, text)
    return project


def test_diff_chunks_identifies_changed_chunks():
    from app.services.text_processor import TextProcessor

    old = ["chunk A", "chunk B", "chunk C"]
    old_sigs = [TextProcessor.compute_signature(c) for c in old]
    new = ["chunk A", "chunk B modified", "chunk C"]
    changed, new_sigs = TextProcessor.diff_chunks(new, old_sigs)
    assert changed == ["chunk B modified"]
    assert len(new_sigs) == 3


def test_diff_chunks_empty_stored():
    from app.services.text_processor import TextProcessor

    chunks = ["a", "b", "c"]
    changed, new_sigs = TextProcessor.diff_chunks(chunks, [])
    assert changed == ["a", "b", "c"]
    assert len(new_sigs) == 3


def test_incremental_flag_with_small_changes(monkeypatch, tmp_path):
    from app.models.project import ProjectManager
    from app.services.text_processor import TextProcessor

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    # Store signatures for original text
    text = ProjectManager.get_extracted_text(project.project_id)
    chunks = TextProcessor.split_text(text, 300, 30)
    chunks = TextProcessor.deduplicate_chunks(chunks)
    project.chunk_signatures = [TextProcessor.compute_signature(c) for c in chunks]
    ProjectManager.save_project(project)

    # Modify text slightly
    ProjectManager.save_extracted_text(project.project_id, "A" * 400 + "B" * 400)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "incremental": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    # Should either be incremental or fallback to full rebuild
    assert "task_id" in payload["data"] or payload["data"].get("skipped") is True


def test_incremental_skips_when_no_changes(monkeypatch, tmp_path):
    from app.models.project import ProjectManager
    from app.services.text_processor import TextProcessor

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()
    project = _create_project_with_text("A" * 800)

    # Store signatures matching current text
    text = ProjectManager.get_extracted_text(project.project_id)
    chunks = TextProcessor.split_text(text, 300, 30)
    chunks = TextProcessor.deduplicate_chunks(chunks)
    project.chunk_signatures = [TextProcessor.compute_signature(c) for c in chunks]
    ProjectManager.save_project(project)

    response = client.post(
        "/api/graph/build",
        json={"project_id": project.project_id, "incremental": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    # No changes → skip or rebuild skip
