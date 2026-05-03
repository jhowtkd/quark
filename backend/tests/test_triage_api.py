"""Tests for triage API endpoints."""

import os
import shutil
import pytest
from app import create_app
from app.models.feedback import FeedbackManager


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    feedback_dir = FeedbackManager.FEEDBACK_DIR
    if os.path.exists(feedback_dir):
        shutil.rmtree(feedback_dir)
    FeedbackManager._instance = None
    # Clean changelogs dir to avoid interference from previous test runs
    changelogs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'changelogs')
    if os.path.exists(changelogs_dir):
        for f in os.listdir(changelogs_dir):
            if f.startswith('beta-test') or f.startswith('beta-api-test'):
                os.remove(os.path.join(changelogs_dir, f))
    with app.test_client() as c:
        yield c


class TestTriageEndpoints:
    """Triage API integration tests."""

    def test_triage_endpoint_manual(self, client):
        # Create feedback
        create_resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 1,
                "comment": "Critical failure test",
            },
        )
        feedback_id = create_resp.get_json()["data"]["feedback_id"]

        # Classify as P0
        resp = client.post(
            f"/api/feedback/{feedback_id}/triage",
            json={"severity": "p0", "notes": "Blocks simulation"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["severity"] == "p0"
        assert data["data"]["converted_to_backlog"] is True

    def test_generate_backlog_endpoint(self, client):
        service_module = __import__('app.services.triage_service', fromlist=['TriageService'])
        TriageService = service_module.TriageService

        # Setup: create and classify P0
        manager = FeedbackManager()
        item = manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 1,
            "comment": "Critical failure for backlog",
        })
        TriageService().classify_feedback(item.feedback_id, "p0")

        resp = client.post("/api/feedback/triage/generate-backlog")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["items_created"] >= 0

    def test_generate_changelog_endpoint(self, client):
        resp = client.post(
            "/api/feedback/triage/generate-changelog",
            json={"since": "2026-01-01", "output_filename": "beta-api-test.md"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "path" in data["data"]
        assert "content_preview" in data["data"]

    def test_auto_classify_endpoint(self, client):
        manager = FeedbackManager()
        manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 1,
            "comment": "Auto classify test",
        })

        resp = client.post("/api/feedback/triage/auto")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["count"] >= 1
        assert isinstance(data["data"]["classified"], list)

    def test_weekly_summary_endpoint(self, client):
        resp = client.get("/api/feedback/triage/weekly-summary?since=2026-01-01")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "total_new" in data["data"]
        assert "by_severity" in data["data"]
        assert "avg_rating" in data["data"]

    def test_latest_changelog_endpoint_empty(self, client):
        resp = client.get("/api/feedback/triage/latest-changelog")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # When no changelog exists, data key may be omitted or null
        assert data.get("data") is None
