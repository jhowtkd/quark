"""
Tests for research approval, rejection, and rerun functionality.

Covers all 9 status transitions:
1. PENDING -> RUNNING
2. RUNNING -> COMPLETED
3. RUNNING -> FAILED
4. COMPLETED -> APPROVED
5. COMPLETED -> PENDING (reject)
6. PENDING -> RERUN_REQUESTED (via rerun creates new run)
7. COMPLETED -> RERUN_REQUESTED
8. New run from rerun: PENDING -> RUNNING
9. FAILED terminal state (cannot approve/reject/rerun original)
"""

import json
import os
import sys
import pytest
import tempfile
import threading
import shutil
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure path setup
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _make_app(monkeypatch, tmp_path):
    """Create app with isolated research directory using monkeypatch."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("ZEP_API_KEY", "test-zep-key")

    from app import create_app
    from app.config import Config
    from app.models.research_run import ResearchRunManager
    from app.models.project import ProjectManager
    from app.models.task import TaskManager

    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(upload_root))
    monkeypatch.setattr(ResearchRunManager, "RESEARCH_DIR", str(upload_root / "research"))
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(upload_root / "projects"))

    # Reset singletons so each test gets fresh state
    TaskManager._instance = None
    ResearchRunManager._instance = None

    return create_app()


def _get_research_dir(run_id: str, research_dir: str) -> str:
    """Get the research run directory path."""
    return os.path.join(research_dir, run_id)


def _get_draft_path(run_id: str, research_dir: str) -> str:
    """Get the draft.md artifact path for a run."""
    return os.path.join(_get_research_dir(run_id, research_dir), 'draft.md')


class TestResearchRunStatus:
    """Test ResearchRunStatus enum has required states."""

    def test_has_required_statuses(self, monkeypatch, tmp_path):
        """Verify all required statuses exist."""
        from app.models.research_run import ResearchRunStatus
        assert hasattr(ResearchRunStatus, "PENDING")
        assert hasattr(ResearchRunStatus, "RUNNING")
        assert hasattr(ResearchRunStatus, "COMPLETED")
        assert hasattr(ResearchRunStatus, "FAILED")
        assert hasattr(ResearchRunStatus, "APPROVED")
        assert hasattr(ResearchRunStatus, "RERUN_REQUESTED")

    def test_status_values(self, monkeypatch, tmp_path):
        """Verify status string values."""
        from app.models.research_run import ResearchRunStatus
        assert ResearchRunStatus.PENDING.value == "pending"
        assert ResearchRunStatus.RUNNING.value == "running"
        assert ResearchRunStatus.COMPLETED.value == "completed"
        assert ResearchRunStatus.FAILED.value == "failed"
        assert ResearchRunStatus.APPROVED.value == "approved"
        assert ResearchRunStatus.RERUN_REQUESTED.value == "rerun_requested"


class TestResearchRunManagerApproval:
    """Test ResearchRunManager approval/rejection methods."""

    def test_approve_run_success(self, monkeypatch, tmp_path):
        """Test approving a COMPLETED run succeeds."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()
        
        # Create a completed run
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        # Verify it's completed
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.COMPLETED
        
        # Approve it
        result = manager.approve_run(run.run_id)
        assert result is True
        
        # Verify status changed
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.APPROVED

    def test_approve_run_not_found(self, monkeypatch, tmp_path):
        """Test approving non-existent run returns False."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        result = manager.approve_run("nonexistent_id")
        assert result is False

    def test_approve_run_wrong_status(self, monkeypatch, tmp_path):
        """Test approving non-COMPLETED run returns False."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        
        # Try to approve a PENDING run
        result = manager.approve_run(run.run_id)
        assert result is False
        
        # Verify status unchanged
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.PENDING


class TestResearchRunManagerRejection:
    """Test ResearchRunManager rejection method."""

    def test_reject_run_success(self, monkeypatch, tmp_path):
        """Test rejecting a run resets it to PENDING."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        # Reject it
        result = manager.reject_run(run.run_id)
        assert result is True
        
        # Verify status reset and metadata updated
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.PENDING
        assert "rejected_at" in run.metadata
        assert run.metadata.get("rejection_count") == 1

    def test_reject_run_not_found(self, monkeypatch, tmp_path):
        """Test rejecting non-existent run returns False."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        result = manager.reject_run("nonexistent_id")
        assert result is False

    def test_reject_run_increments_counter(self, monkeypatch, tmp_path):
        """Test multiple rejections increment counter."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        # First rejection
        manager.reject_run(run.run_id)
        run = manager.get_run(run.run_id)
        assert run.metadata.get("rejection_count") == 1
        
        # Complete again and reject
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        manager.reject_run(run.run_id)
        run = manager.get_run(run.run_id)
        assert run.metadata.get("rejection_count") == 2


class TestResearchRunManagerRerun:
    """Test ResearchRunManager rerun method."""

    def test_request_rerun_creates_new_run(self, monkeypatch, tmp_path):
        """Test rerun creates new run with feedback."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        manager = ResearchRunManager()
        original = manager.create_run("Original query")
        manager.complete_run(original.run_id, "/path/to/draft.md", "brave")
        
        # Request rerun with feedback
        new_run = manager.request_rerun(original.run_id, "Please be more detailed")
        assert new_run is not None
        assert new_run.run_id != original.run_id
        
        # Verify original is marked as rerun requested
        original = manager.get_run(original.run_id)
        assert original.status == ResearchRunStatus.RERUN_REQUESTED
        assert original.metadata.get("feedback") == "Please be more detailed"
        assert original.metadata.get("feedback_count") == 1
        
        # Verify new run has combined query
        assert "Original query" in new_run.query
        assert "Please be more detailed" in new_run.query
        assert new_run.metadata.get("original_run_id") == original.run_id

    def test_request_rerun_not_found(self, monkeypatch, tmp_path):
        """Test rerun of non-existent run returns None."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        manager = ResearchRunManager()
        result = manager.request_rerun("nonexistent_id", "feedback")
        assert result is None


class TestApprovalEndpoint:
    """Test POST /api/research/approve/<run_id> endpoint."""

    def test_approve_completed_run_success(self, monkeypatch, tmp_path):
        """Test approving a completed run with valid draft."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()
        
        # Create a run
        run = manager.create_run("Test query")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        
        # Write valid draft.md
        draft_path = _get_draft_path(run.run_id, research_dir)
        draft_content = textwrap.dedent("""\
            # Deep Research: Test query

            ## Summary
            Valid summary content.

            ## Claims
            1. Claim one.

            ## Sources
            - Source 1
            """)
        with open(draft_path, "w") as f:
            f.write(draft_content)
        
        manager.complete_run(run.run_id, draft_path, "brave")
        
        # Approve via API
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"

    def test_approve_run_not_found(self, monkeypatch, tmp_path):
        """Test approving non-existent run returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()
        
        response = client.post("/api/research/approve/nonexistent_id")
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert data["success"] is False

    def test_approve_non_completed_run(self, monkeypatch, tmp_path):
        """Test approving non-COMPLETED run returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "completed" in data["error"].lower()

    def test_approve_missing_draft(self, monkeypatch, tmp_path):
        """Test approving when draft.md is missing fails closed."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        # Don't create draft.md file
        
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "missing" in data["error"].lower() or "not found" in data["error"].lower()
        
        # Verify run is marked as failed
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.FAILED

    def test_approve_incomplete_draft(self, monkeypatch, tmp_path):
        """Test approving incomplete draft (missing sections) fails closed."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        
        # Write incomplete draft - missing Sources section
        draft_content = textwrap.dedent("""\
            # Deep Research: Test query

            ## Summary
            Valid summary.

            ## Claims
            1. Claim.
            """)
        with open(draft_path, "w") as f:
            f.write(draft_content)
        
        manager.complete_run(run.run_id, draft_path, "brave")
        
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "missing" in data["error"].lower()
        
        # Verify run is marked as failed
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.FAILED


class TestRejectionEndpoint:
    """Test POST /api/research/reject/<run_id> endpoint."""

    def test_reject_run_success(self, monkeypatch, tmp_path):
        """Test rejecting a run resets it to PENDING."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        response = client.post(f"/api/research/reject/{run.run_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "pending"

    def test_reject_run_not_found(self, monkeypatch, tmp_path):
        """Test rejecting non-existent run returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()
        
        response = client.post("/api/research/reject/nonexistent_id")
        assert response.status_code == 404


class TestRerunEndpoint:
    """Test POST /api/research/rerun/<run_id> endpoint."""

    def test_rerun_creates_new_run(self, monkeypatch, tmp_path):
        """Test rerun creates new run and starts processing."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        manager = ResearchRunManager()
        original = manager.create_run("Original query")
        manager.complete_run(original.run_id, "/path/to/draft.md", "brave")
        
        response = client.post(
            f"/api/research/rerun/{original.run_id}",
            json={"feedback": "Please add more sources"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "new_run_id" in data["data"]
        assert "task_id" in data["data"]
        assert data["data"]["original_run_id"] == original.run_id

    def test_rerun_requires_feedback(self, monkeypatch, tmp_path):
        """Test rerun without feedback returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        response = client.post(
            f"/api/research/rerun/{run.run_id}",
            json={"feedback": ""}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "feedback" in data["error"].lower()

    def test_rerun_missing_feedback_field(self, monkeypatch, tmp_path):
        """Test rerun without feedback field returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        
        response = client.post(f"/api/research/rerun/{run.run_id}", json={})
        assert response.status_code == 400

    def test_rerun_not_found(self, monkeypatch, tmp_path):
        """Test rerun of non-existent run returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()
        
        response = client.post(
            "/api/research/rerun/nonexistent_id",
            json={"feedback": "test"}
        )
        assert response.status_code == 404


class TestStatusTransitions:
    """Integration tests for complete status transition flows."""

    def test_full_approval_flow(self, monkeypatch, tmp_path):
        """Test complete flow: create -> complete -> approve."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()
        
        # Create run
        run = manager.create_run("Integration test query")
        assert run.status == ResearchRunStatus.PENDING
        
        # Simulate completion
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        draft_content = textwrap.dedent("""\
            # Deep Research: Integration test

            ## Summary
            Test summary.

            ## Claims
            1. Test claim.

            ## Sources
            - Source 1
            """)
        with open(draft_path, "w") as f:
            f.write(draft_content)
        
        manager.complete_run(run.run_id, draft_path, "tavily")
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.COMPLETED
        
        # Approve via API
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 200
        
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.APPROVED

    def test_reject_and_resubmit_flow(self, monkeypatch, tmp_path):
        """Test flow: complete -> reject -> rerun -> complete -> approve."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()
        
        # Create and complete original
        run = manager.create_run("Original query")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        draft_content = textwrap.dedent("""\
            # Deep Research: Original

            ## Summary
            Original summary.

            ## Claims
            1. Claim.

            ## Sources
            - Source
            """)
        with open(draft_path, "w") as f:
            f.write(draft_content)
        manager.complete_run(run.run_id, draft_path, "brave")
        
        # Reject
        response = client.post(f"/api/research/reject/{run.run_id}")
        assert response.status_code == 200
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.PENDING
        assert run.metadata.get("rejection_count") == 1
        
        # Rerun
        response = client.post(
            f"/api/research/rerun/{run.run_id}",
            json={"feedback": "Make it more comprehensive"}
        )
        assert response.status_code == 200
        data = response.get_json()
        new_run_id = data["data"]["new_run_id"]
        
        # Verify original marked as rerun_requested
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.RERUN_REQUESTED

    def test_failed_run_cannot_be_approved(self, monkeypatch, tmp_path):
        """Test that FAILED runs cannot be approved."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager, ResearchRunStatus
        
        client = app.test_client()
        manager = ResearchRunManager()
        run = manager.create_run("Test query")
        manager.fail_run(run.run_id, "Test error")
        
        response = client.post(f"/api/research/approve/{run.run_id}")
        assert response.status_code == 400
        
        run = manager.get_run(run.run_id)
        assert run.status == ResearchRunStatus.FAILED  # Unchanged


class TestGenerateOntologyFromText:
    """Test POST /api/graph/ontology/generate-from-text/<project_id> endpoint."""

    def test_generate_from_text_creates_ontology(self, monkeypatch, tmp_path):
        """Generating ontology from existing text succeeds."""
        app = _make_app(monkeypatch, tmp_path)
        from app.services.ontology_generator import OntologyGenerator

        client = app.test_client()

        # Create project with extracted text
        from app.models.project import ProjectManager
        project = ProjectManager.create_project(name="Research Project")
        text_content = "This is a test document about social media simulation."
        ProjectManager.save_extracted_text(project.project_id, text_content)

        # Mock the ontology generator to avoid LLM calls
        mock_ontology = {
            "entity_types": [
                {"name": "Person", "description": "A person", "attributes": [], "examples": []},
                {"name": "Organization", "description": "An org", "attributes": [], "examples": []},
            ],
            "edge_types": [
                {"name": "WORKS_FOR", "description": "Works for", "source_targets": [], "attributes": []},
            ],
            "analysis_summary": "Test summary",
        }
        with patch.object(OntologyGenerator, 'generate', return_value=mock_ontology):
            response = client.post(
                f"/api/graph/ontology/generate-from-text/{project.project_id}",
                json={"simulation_requirement": "Simulate social media discourse"}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["project_id"] == project.project_id
        assert data["data"]["text_char_count"] == len(text_content)
        assert data["data"]["entity_count"] == 2
        assert data["data"]["edge_count"] == 1
        assert "generation_time_ms" in data["data"]

    def test_generate_from_text_missing_project(self, monkeypatch, tmp_path):
        """Generating from nonexistent project returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()

        response = client.post(
            "/api/graph/ontology/generate-from-text/nonexistent",
            json={"simulation_requirement": "Test requirement"}
        )
        assert response.status_code == 404

    def test_generate_from_text_missing_requirement(self, monkeypatch, tmp_path):
        """Generating without simulation_requirement returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.project import ProjectManager

        client = app.test_client()
        project = ProjectManager.create_project(name="Test Project")
        ProjectManager.save_extracted_text(project.project_id, "Some text")

        response = client.post(
            f"/api/graph/ontology/generate-from-text/{project.project_id}",
            json={}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "requirement" in data["error"].lower()

    def test_generate_from_text_no_extracted_text(self, monkeypatch, tmp_path):
        """Generating when project has no extracted text returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.project import ProjectManager

        client = app.test_client()
        project = ProjectManager.create_project(name="Empty Project")

        response = client.post(
            f"/api/graph/ontology/generate-from-text/{project.project_id}",
            json={"simulation_requirement": "Test requirement"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "text" in data["error"].lower()


class TestPromoteEndpoint:
    """Test POST /api/research/promote/<run_id> endpoint."""

    def test_promote_approved_run_creates_project(self, monkeypatch, tmp_path):
        """Promoting approved run without project_id creates new project."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create and approve a run
        run = manager.create_run("Promote test query")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = "# Research Content\n\nSome findings."
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Promote without project_id (creates new project)
        response = client.post(f"/api/research/promote/{run.run_id}", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["run_id"] == run.run_id
        assert "project_id" in data["data"]
        assert data["data"]["merge_mode"] == "created"
        assert data["data"]["promoted_char_count"] == len(research_content)

        # Verify project was created with content
        project_id = data["data"]["project_id"]
        project = ProjectManager.get_project(project_id)
        assert project is not None
        assert ProjectManager.get_extracted_text(project_id) == research_content

    def test_promote_approved_run_to_existing_project(self, monkeypatch, tmp_path):
        """Promoting approved run to existing project with text appends."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create existing project with text
        existing_project = ProjectManager.create_project(name="Existing Project")
        existing_text = "# Existing Content\n\nPrevious research."
        ProjectManager.save_extracted_text(existing_project.project_id, existing_text)

        # Create and approve a run
        run = manager.create_run("Promote to existing test")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = "# New Research\n\nNew findings."
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Promote to existing project
        response = client.post(
            f"/api/research/promote/{run.run_id}",
            json={"project_id": existing_project.project_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["project_id"] == existing_project.project_id
        assert data["data"]["merge_mode"] == "append"

        # Verify text was appended with separator (existing + separator + research)
        merged_text = ProjectManager.get_extracted_text(existing_project.project_id)
        assert merged_text.startswith(existing_text)
        assert research_content in merged_text
        assert merged_text.endswith(research_content)

    def test_promote_to_project_with_no_existing_text(self, monkeypatch, tmp_path):
        """Promoting to project without existing text uses new merge mode."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create project without extracted text
        empty_project = ProjectManager.create_project(name="Empty Project")

        # Create and approve a run
        run = manager.create_run("Promote to empty project")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = "# Research\n\nContent."
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Promote to empty project
        response = client.post(
            f"/api/research/promote/{run.run_id}",
            json={"project_id": empty_project.project_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["merge_mode"] == "new"

    def test_promote_non_approved_run_returns_400(self, monkeypatch, tmp_path):
        """Promoting non-APPROVED run returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager

        client = app.test_client()
        manager = ResearchRunManager()

        # Create but don't approve run
        run = manager.create_run("Pending run")
        response = client.post(f"/api/research/promote/{run.run_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "approved" in data["error"].lower()

        # Complete but don't approve
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")
        response = client.post(f"/api/research/promote/{run.run_id}")
        assert response.status_code == 400

    def test_promote_nonexistent_run_returns_404(self, monkeypatch, tmp_path):
        """Promoting nonexistent run returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()

        response = client.post("/api/research/promote/nonexistent_run")
        assert response.status_code == 404

    def test_promote_approved_run_nonexistent_project(self, monkeypatch, tmp_path):
        """Promoting to nonexistent project returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create and approve a run
        run = manager.create_run("Test query")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        with open(draft_path, "w") as f:
            f.write("# Research")
        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Promote to nonexistent project
        response = client.post(
            f"/api/research/promote/{run.run_id}",
            json={"project_id": "proj_nonexistent"}
        )
        assert response.status_code == 404


class TestCreateProjectEndpoint:
    """Test POST /api/research/create-project/<run_id> endpoint."""

    def test_create_project_from_approved_run(self, monkeypatch, tmp_path):
        """Creating project from approved run succeeds."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create and approve a run
        run = manager.create_run("Create project test")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = "# Deep Research: Create project test\n\n## Summary\nTest."
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Create project from research
        response = client.post(f"/api/research/create-project/{run.run_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["run_id"] == run.run_id
        assert "project_id" in data["data"]
        assert "project_name" in data["data"]
        assert "Research:" in data["data"]["project_name"]

        # Verify project exists and has content
        project_id = data["data"]["project_id"]
        project = ProjectManager.get_project(project_id)
        assert project is not None
        assert ProjectManager.get_extracted_text(project_id) == research_content

        # Verify stub ontology is set
        assert project.ontology == {"entity_types": [], "edge_types": []}

    def test_create_project_from_non_approved_run(self, monkeypatch, tmp_path):
        """Creating project from non-APPROVED run returns 400."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager

        client = app.test_client()
        manager = ResearchRunManager()

        # Create run in COMPLETED state but not approved
        run = manager.create_run("Pending project")
        manager.complete_run(run.run_id, "/path/to/draft.md", "brave")

        response = client.post(f"/api/research/create-project/{run.run_id}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "approved" in data["error"].lower()

    def test_create_project_nonexistent_run(self, monkeypatch, tmp_path):
        """Creating project from nonexistent run returns 404."""
        app = _make_app(monkeypatch, tmp_path)
        client = app.test_client()

        response = client.post("/api/research/create-project/nonexistent_run")
        assert response.status_code == 404

    def test_create_project_sets_stub_ontology(self, monkeypatch, tmp_path):
        """Created project has stub ontology with empty entity/edge types."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create and approve run
        run = manager.create_run("Ontology stub test")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        with open(draft_path, "w") as f:
            f.write("# Content")
        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        response = client.post(f"/api/research/create-project/{run.run_id}")
        assert response.status_code == 200

        project_id = response.get_json()["data"]["project_id"]
        project = ProjectManager.get_project(project_id)

        assert project.ontology is not None
        assert "entity_types" in project.ontology
        assert "edge_types" in project.ontology
        assert project.ontology["entity_types"] == []
        assert project.ontology["edge_types"] == []


class TestResearchOnlyGraphFlow:
    """
    Integration tests for the research-only graph build flow:
    create-project -> generate-ontology-from-text -> build-graph preview

    Covers the complete happy path for research-only projects.
    """

    def test_research_only_project_ontology_generation_produces_populated_ontology(self, monkeypatch, tmp_path):
        """Research-only project generate-ontology-from-text produces non-stub ontology."""
        app = _make_app(monkeypatch, tmp_path)
        from app.services.ontology_generator import OntologyGenerator
        from app.models.project import ProjectManager

        client = app.test_client()

        # Create project via create-project endpoint (simulating research promotion)
        from app.models.research_run import ResearchRunManager
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create and approve a run with research content
        run = manager.create_run("Social media simulation research")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = textwrap.dedent("""\
            # Deep Research: Social media simulation

            ## Summary
            Social media platforms simulate human behavior through agent-based models.

            ## Claims
            1. Agents form echo chambers through preferential attachment
            2. Opinion dynamics follow bounded confidence models
            3. Network topology evolves via triadic closure

            ## Sources
            - Watts & Strogatz (1998) Small-world networks
            - Hegselmann & Krause (2002) Bounded confidence model
            """)
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Create project from research
        response = client.post(f"/api/research/create-project/{run.run_id}")
        assert response.status_code == 200
        project_id = response.get_json()["data"]["project_id"]

        # Mock the ontology generator to return a populated ontology
        mock_ontology = {
            "entity_types": [
                {"name": "Agent", "description": "A simulated user", "attributes": [], "examples": []},
                {"name": "Opinion", "description": "Agent viewpoint", "attributes": [], "examples": []},
                {"name": "Network", "description": "Social network structure", "attributes": [], "examples": []},
            ],
            "edge_types": [
                {"name": "INTERACTS_WITH", "description": "Agent interaction", "source_targets": [], "attributes": []},
                {"name": "INFLUENCES", "description": "Opinion influence", "source_targets": [], "attributes": []},
            ],
            "analysis_summary": "Three main entity types emerge from the research",
        }
        with patch.object(OntologyGenerator, 'generate', return_value=mock_ontology):
            # Generate ontology from text
            response = client.post(
                f"/api/graph/ontology/generate-from-text/{project_id}",
                json={"simulation_requirement": "Simulate social media discourse dynamics"}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["entity_count"] == 3
        assert data["data"]["edge_count"] == 2
        assert data["data"]["text_char_count"] == len(research_content)

        # Verify ontology is populated (not stub)
        project = ProjectManager.get_project(project_id)
        assert project.ontology is not None
        assert len(project.ontology["entity_types"]) == 3
        assert len(project.ontology["edge_types"]) == 2
        assert project.ontology != {"entity_types": [], "edge_types": []}

    def test_promote_endpoint_appends_research_after_existing_text(self, monkeypatch, tmp_path):
        """Promote endpoint appends research after existing text (not prepends)."""
        app = _make_app(monkeypatch, tmp_path)
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Create existing project with text
        existing_project = ProjectManager.create_project(name="Existing Project")
        existing_text = "# Existing Research\n\nPreliminary findings about agent behavior."
        ProjectManager.save_extracted_text(existing_project.project_id, existing_text)

        # Create and approve a run
        run = manager.create_run("Additional research findings")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = textwrap.dedent("""\
            # Deep Research: Additional Findings

            ## Summary
            New evidence supports multi-agent coordination.

            ## Claims
            1. Coordination emerges from local rules
            2. Scale-free networks exhibit robustness

            ## Sources
            - Barabási (1999) Scale-free networks
            """)
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Promote to existing project
        response = client.post(
            f"/api/research/promote/{run.run_id}",
            json={"project_id": existing_project.project_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["merge_mode"] == "append"

        # Verify text is APPENDED (existing + separator + research)
        merged_text = ProjectManager.get_extracted_text(existing_project.project_id)
        assert merged_text.startswith(existing_text), "Existing text should be at start"
        assert "# Deep Research: Additional Findings" in merged_text
        # The research content should appear AFTER existing text
        existing_pos = merged_text.find(existing_text)
        research_pos = merged_text.find("# Deep Research: Additional Findings")
        assert existing_pos < research_pos, "Research should be appended after existing text"
        # Research should be at end (allowing for trailing whitespace/newlines from file write)
        assert merged_text.rstrip().endswith(research_content.strip()), "Research should be at end"

    def test_research_only_full_flow_create_project_generate_ontology_preview_succeeds(self, monkeypatch, tmp_path):
        """Research-only project complete flow: create-project -> generate-ontology -> build-graph preview succeeds."""
        app = _make_app(monkeypatch, tmp_path)
        from app.services.ontology_generator import OntologyGenerator
        from app.models.research_run import ResearchRunManager
        from app.models.project import ProjectManager

        client = app.test_client()
        research_dir = str(tmp_path / "uploads" / "research")
        manager = ResearchRunManager()

        # Step 1: Create project from research (simulate promote/create-project flow)
        run = manager.create_run("Complete research flow test")
        run_dir = _get_research_dir(run.run_id, research_dir)
        os.makedirs(run_dir, exist_ok=True)
        draft_path = _get_draft_path(run.run_id, research_dir)
        research_content = textwrap.dedent("""\
            # Deep Research: Multi-Agent Systems

            ## Summary
            Multi-agent systems model complex social behaviors through autonomous entities.

            ## Claims
            1. Emergent behavior arises from simple local interactions
            2. Network effects amplify individual decisions
            3. Temporal dynamics shape system evolution

            ## Sources
            - Epstein & Axtell (1996) Growing Artificial Societies
            - Miller & Page (2007) Complex Adaptive Systems
            """)
        with open(draft_path, "w") as f:
            f.write(research_content)

        manager.complete_run(run.run_id, draft_path, "brave")
        manager.approve_run(run.run_id)

        # Create project from research
        response = client.post(f"/api/research/create-project/{run.run_id}")
        assert response.status_code == 200, f"create-project failed: {response.get_json()}"
        project_id = response.get_json()["data"]["project_id"]

        # Step 2: Generate ontology from text
        mock_ontology = {
            "entity_types": [
                {"name": "Agent", "description": "Autonomous entity", "attributes": [], "examples": []},
                {"name": "Network", "description": "Connection structure", "attributes": [], "examples": []},
                {"name": "State", "description": "System state", "attributes": [], "examples": []},
            ],
            "edge_types": [
                {"name": "INTERACTS", "description": "Agent interaction", "source_targets": [], "attributes": []},
            ],
            "analysis_summary": "Three entity types identified",
        }
        with patch.object(OntologyGenerator, 'generate', return_value=mock_ontology):
            response = client.post(
                f"/api/graph/ontology/generate-from-text/{project_id}",
                json={"simulation_requirement": "Simulate multi-agent social system"}
            )

        assert response.status_code == 200, f"generate-ontology failed: {response.get_json()}"
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["entity_count"] == 3
        assert data["data"]["edge_count"] == 1

        # Step 3: Build graph preview succeeds
        response = client.post(
            "/api/graph/build",
            json={
                "project_id": project_id,
                "preview": True,
                "chunk_size": 300,
                "chunk_overlap": 30
            }
        )

        assert response.status_code == 200, f"build-graph preview failed: {response.get_json()}"
        data = response.get_json()
        assert data["success"] is True
        assert "ontology_guardrails" in data["data"]
        assert "chunk_count" in data["data"]
        assert "estimated_total_chars" in data["data"]
        assert "estimated_credits" in data["data"]

        # Verify final project state
        project = ProjectManager.get_project(project_id)
        assert project.status.value == "ontology_generated"
        assert project.ontology is not None
        assert len(project.ontology["entity_types"]) == 3
