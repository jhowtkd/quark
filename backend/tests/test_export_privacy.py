"""Tests that exported report/simulation data does not leak sensitive fields."""

import json
from unittest.mock import patch

import pytest

from app import create_app
from app.services.report_agent import Report, ReportOutline, ReportSection, ReportStatus
from app.utils.response import error_response


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestReportExportPrivacy:
    """Verify report API responses exclude llm_raw_response, prompt_text, traceback."""

    def _make_report(self) -> Report:
        return Report(
            report_id="report_test_001",
            simulation_id="sim_test_001",
            graph_id="graph_test_001",
            simulation_requirement="Test requirement",
            status=ReportStatus.COMPLETED,
            outline=ReportOutline(
                title="Test Report",
                summary="Summary",
                sections=[
                    ReportSection(
                        title="Intro",
                        content="Hello",
                        status=ReportStatus.COMPLETED,
                    )
                ],
            ),
            markdown_content="# Hello",
            created_at="2026-05-02T10:00:00",
            completed_at="2026-05-02T11:00:00",
            error=None,
        )

    def test_report_to_dict_excludes_sensitive_fields(self):
        report = self._make_report()
        data = report.to_dict()
        json_str = json.dumps(data)
        assert "llm_raw_response" not in json_str
        assert "prompt_text" not in json_str
        assert "traceback" not in json_str
        assert "internal_metadata" not in json_str

    def test_get_report_endpoint_excludes_sensitive_fields(self, client):
        report = self._make_report()
        with patch("app.api.report.ReportManager.get_report", return_value=report):
            resp = client.get("/api/report/report_test_001")
            assert resp.status_code == 200
            data = resp.get_json()
            json_str = json.dumps(data)
            assert "llm_raw_response" not in json_str
            assert "prompt_text" not in json_str
            assert "traceback" not in json_str
            assert "internal_metadata" not in json_str

    def test_get_report_by_simulation_endpoint_excludes_sensitive_fields(self, client):
        report = self._make_report()
        with patch(
            "app.api.report.ReportManager.get_report_by_simulation", return_value=report
        ):
            resp = client.get("/api/report/by-simulation/sim_test_001")
            assert resp.status_code == 200
            data = resp.get_json()
            json_str = json.dumps(data)
            assert "llm_raw_response" not in json_str
            assert "prompt_text" not in json_str
            assert "traceback" not in json_str
            assert "internal_metadata" not in json_str


class TestErrorResponsePrivacy:
    """Verify error responses never include traceback."""

    def test_error_response_excludes_traceback(self):
        resp, code = error_response("Something went wrong", 500)
        assert "traceback" not in str(resp).lower()
        assert "traceback" not in json.dumps(resp).lower()
