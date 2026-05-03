"""Tests for feedback API endpoints."""

import os
import shutil
import pytest
from app import create_app
from app.models.feedback import FeedbackManager


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    # Clean feedback directory before each test to avoid singleton state bleeding
    feedback_dir = FeedbackManager.FEEDBACK_DIR
    if os.path.exists(feedback_dir):
        shutil.rmtree(feedback_dir)
    FeedbackManager._instance = None
    with app.test_client() as c:
        yield c


class TestFeedbackAPI:
    """Feedback CRUD and stats endpoints."""

    def test_create_feedback_success(self, client):
        resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 2,
                "comment": "Simulacao parou no round 45 sem erro visivel",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["feedback_id"].startswith("fb_")
        assert "created_at" in data["data"]

    def test_create_feedback_validation_error_missing_rating(self, client):
        resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
            },
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "rating" in data["error"].lower()

    def test_create_feedback_comment_required_for_low_rating(self, client):
        resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 2,
                "comment": "",
            },
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "comentario" in data["error"].lower()

    def test_list_feedback_filter_by_category(self, client):
        # Create 2 bugs
        for _ in range(2):
            client.post(
                "/api/feedback",
                json={
                    "stage": "simulation",
                    "category": "bug",
                    "rating": 2,
                    "comment": "Bug report test min 10 chars",
                },
            )
        # Create 1 suggestion
        client.post(
            "/api/feedback",
            json={
                "stage": "report",
                "category": "suggestion",
                "rating": 5,
                "comment": "Great feature suggestion here",
            },
        )

        resp = client.get("/api/feedback?category=bug")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["count"] == 2
        for item in data["data"]["items"]:
            assert item["category"] == "bug"

    def test_get_feedback_summary(self, client):
        # Create 3 feedbacks
        client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 1,
                "comment": "Critical failure on simulation",
            },
        )
        client.post(
            "/api/feedback",
            json={
                "stage": "report",
                "category": "suggestion",
                "rating": 4,
                "comment": "Would love to see more charts",
            },
        )
        client.post(
            "/api/feedback",
            json={
                "stage": "graph_build",
                "category": "ux_confusion",
                "rating": 3,
                "comment": "Interface is a bit confusing",
            },
        )

        resp = client.get("/api/feedback/stats/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        assert data["data"]["avg_rating"] == 2.7
        assert data["data"]["by_category"]["bug"] == 1
        assert data["data"]["by_category"]["suggestion"] == 1
        assert data["data"]["by_category"]["ux_confusion"] == 1
        assert data["data"]["by_stage"]["simulation"] == 1
        assert data["data"]["by_stage"]["report"] == 1
        assert data["data"]["by_stage"]["graph_build"] == 1

    def test_get_feedback_by_id(self, client):
        create_resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 2,
                "comment": "Test feedback for get by id",
            },
        )
        feedback_id = create_resp.get_json()["data"]["feedback_id"]

        resp = client.get(f"/api/feedback/{feedback_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["feedback_id"] == feedback_id
        assert data["data"]["category"] == "bug"

    def test_get_feedback_not_found(self, client):
        resp = client.get("/api/feedback/fb_nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_update_feedback_severity(self, client):
        create_resp = client.post(
            "/api/feedback",
            json={
                "stage": "simulation",
                "category": "bug",
                "rating": 1,
                "comment": "Critical bug needs triage",
            },
        )
        feedback_id = create_resp.get_json()["data"]["feedback_id"]

        resp = client.put(
            f"/api/feedback/{feedback_id}",
            json={"severity": "p0", "triage_notes": "Blocks health simulations"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "updated_at" in data["data"]

        # Verify update
        get_resp = client.get(f"/api/feedback/{feedback_id}")
        assert get_resp.get_json()["data"]["severity"] == "p0"
        assert get_resp.get_json()["data"]["triage_notes"] == "Blocks health simulations"
