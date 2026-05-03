"""Tests for TriageService auto-classification heuristics and backlog generation."""

import os
import shutil
import pytest
from app import create_app
from app.models.feedback import FeedbackManager, FeedbackSeverity, FeedbackCategory
from app.services.triage_service import TriageService


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    feedback_dir = FeedbackManager.FEEDBACK_DIR
    if os.path.exists(feedback_dir):
        shutil.rmtree(feedback_dir)
    FeedbackManager._instance = None
    with app.test_client() as c:
        yield c


class TestAutoClassifyHeuristics:
    """Verify heuristic rules for auto-classification."""

    def test_auto_classify_p0_bug_rating_1(self, client):
        service = TriageService()
        manager = FeedbackManager()

        item = manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 1,
            "comment": "Critical crash on startup",
        })

        classified = service.auto_classify()
        assert item.feedback_id in classified

        updated = manager.get_feedback(item.feedback_id)
        assert updated.severity == FeedbackSeverity.P0

    def test_auto_classify_p1_bug_rating_2(self, client):
        service = TriageService()
        manager = FeedbackManager()

        item = manager.create_feedback({
            "stage": "report",
            "category": "bug",
            "rating": 2,
            "comment": "Report data is inconsistent",
        })

        classified = service.auto_classify()
        assert item.feedback_id in classified

        updated = manager.get_feedback(item.feedback_id)
        assert updated.severity == FeedbackSeverity.P1

    def test_auto_classify_p2_ux_confusion(self, client):
        service = TriageService()
        manager = FeedbackManager()

        item = manager.create_feedback({
            "stage": "graph_build",
            "category": "ux_confusion",
            "rating": 3,
            "comment": "I do not understand the graph layout",
        })

        classified = service.auto_classify()
        assert item.feedback_id in classified

        updated = manager.get_feedback(item.feedback_id)
        assert updated.severity == FeedbackSeverity.P2

    def test_auto_classify_p3_suggestion(self, client):
        service = TriageService()
        manager = FeedbackManager()

        item = manager.create_feedback({
            "stage": "report",
            "category": "suggestion",
            "rating": 5,
            "comment": "Add dark mode support",
        })

        classified = service.auto_classify()
        assert item.feedback_id in classified

        updated = manager.get_feedback(item.feedback_id)
        assert updated.severity == FeedbackSeverity.P3

    def test_auto_classify_p3_positive_rating(self, client):
        service = TriageService()
        manager = FeedbackManager()

        item = manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 4,
            "comment": "Minor glitch but overall good",
        })

        classified = service.auto_classify()
        assert item.feedback_id in classified

        updated = manager.get_feedback(item.feedback_id)
        assert updated.severity == FeedbackSeverity.P3


class TestGenerateBacklog:
    """Verify backlog generation from P0/P1 items."""

    def test_generate_backlog_creates_jsonl(self, client):
        service = TriageService()
        manager = FeedbackManager()

        # Create P0 and P1 items via auto-classify (does NOT mark converted_to_backlog)
        manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 1,
            "comment": "Critical crash on startup",
        })
        manager.create_feedback({
            "stage": "report",
            "category": "bug",
            "rating": 2,
            "comment": "Report data is inconsistent",
        })

        # Auto-classify to set severity without marking converted
        service.auto_classify()

        items = service.generate_backlog_items()
        assert len(items) == 2

        # Verify JSONL file exists
        backlog_dir = os.path.join(FeedbackManager.FEEDBACK_DIR, 'backlog')
        jsonl_files = [f for f in os.listdir(backlog_dir) if f.endswith('.jsonl')]
        assert len(jsonl_files) == 1

        with open(os.path.join(backlog_dir, jsonl_files[0]), 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_generate_backlog_skips_already_converted(self, client):
        service = TriageService()
        manager = FeedbackManager()

        manager.create_feedback({
            "stage": "simulation",
            "category": "bug",
            "rating": 1,
            "comment": "Critical crash",
        })
        service.auto_classify()

        # First generation
        items1 = service.generate_backlog_items()
        assert len(items1) == 1

        # Second generation should skip
        items2 = service.generate_backlog_items()
        assert len(items2) == 0


class TestGenerateChangelog:
    """Verify changelog markdown generation."""

    def test_generate_changelog_creates_markdown(self, client):
        from app.services.changelog_service import ChangelogService

        service = TriageService()
        changelog_service = ChangelogService()
        manager = FeedbackManager()

        # Create 3 feedbacks with different severities
        manager.create_feedback({
            "stage": "simulation", "category": "bug", "rating": 1,
            "comment": "Crash on startup",
        })
        manager.create_feedback({
            "stage": "report", "category": "suggestion", "rating": 5,
            "comment": "Add export feature",
        })
        manager.create_feedback({
            "stage": "graph_build", "category": "ux_confusion", "rating": 3,
            "comment": "Graph is hard to read",
        })

        # Auto-classify
        service.auto_classify()

        output_path = os.path.join(FeedbackManager.FEEDBACK_DIR, 'test-changelog.md')
        path = changelog_service.generate_changelog("2026-01-01T00:00:00", output_path)

        assert os.path.exists(path)
        with open(path, 'r') as f:
            content = f.read()
        assert "# Changelog Beta" in content
