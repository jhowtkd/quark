"""Tests for report retry-section API endpoint."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestReportRetryApi:
    """Verify POST /api/report/<report_id>/retry-section endpoint."""

    def test_retry_section_valid_returns_200_and_retrying(self, client, monkeypatch):
        """Valid section_index returns 200 with status 'retrying'."""
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_report",
            lambda rid: type("R", (), {
                "report_id": rid,
                "simulation_id": "sim_1",
                "graph_id": "g1",
                "simulation_requirement": "test",
                "status": type("S", (), {"value": "failed"})(),
                "outline": type("O", (), {
                    "title": "T",
                    "summary": "S",
                    "sections": [
                        type("Sec", (), {"title": "Sec1", "status": type("S", (), {"value": "failed"})(), "content": "", "error_message": "err", "retry_count": 0})()
                    ]
                })(),
            })()
        )
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_progress",
            lambda rid: {
                "status": "failed",
                "progress": 50,
                "failed_sections": [
                    {"section_index": 1, "section_title": "Sec1", "error_message": "err", "failed_at": datetime.now().isoformat()}
                ],
                "completed_sections": []
            }
        )
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_generated_sections",
            lambda rid: []
        )
        monkeypatch.setattr(
            "app.api.report.ReportManager.update_progress",
            lambda *a, **kw: None
        )

        resp = client.post('/api/report/report_123/retry-section', json={"section_index": 1})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "retrying"
        assert data["data"]["section_index"] == 1

    def test_retry_section_missing_index_returns_400(self, client, monkeypatch):
        """Missing section_index returns 400."""
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_report",
            lambda rid: type("R", (), {"report_id": rid})()
        )

        resp = client.post('/api/report/report_123/retry-section', json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_retry_section_invalid_index_returns_400(self, client, monkeypatch):
        """Non-integer section_index returns 400."""
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_report",
            lambda rid: type("R", (), {"report_id": rid})()
        )

        resp = client.post('/api/report/report_123/retry-section', json={"section_index": "abc"})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_retry_section_report_not_found_returns_404(self, client, monkeypatch):
        """Retry on nonexistent report returns 404."""
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_report",
            lambda rid: None
        )

        resp = client.post('/api/report/report_missing/retry-section', json={"section_index": 1})
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_retry_section_not_failed_returns_400(self, client, monkeypatch):
        """Retry on a section that is not in failed_sections returns 400."""
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_report",
            lambda rid: type("R", (), {
                "report_id": rid,
                "simulation_id": "sim_1",
                "graph_id": "g1",
                "simulation_requirement": "test",
                "status": type("S", (), {"value": "completed"})(),
                "outline": type("O", (), {
                    "title": "T",
                    "summary": "S",
                    "sections": [
                        type("Sec", (), {"title": "Sec1", "status": type("S", (), {"value": "completed"})(), "content": "ok", "error_message": None, "retry_count": 0})()
                    ]
                })(),
            })()
        )
        monkeypatch.setattr(
            "app.api.report.ReportManager.get_progress",
            lambda rid: {
                "status": "completed",
                "progress": 100,
                "failed_sections": [],
                "completed_sections": ["Sec1"]
            }
        )

        resp = client.post('/api/report/report_123/retry-section', json={"section_index": 1})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
