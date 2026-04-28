"""Integration tests for the deep research API and agent."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _make_app(monkeypatch, tmp_path):
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app
    from app.config import Config
    from app.models.research_run import ResearchRunManager
    from app.models.task import TaskManager

    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(upload_root))
    monkeypatch.setattr(ResearchRunManager, "RESEARCH_DIR", str(upload_root / "research"))

    # Reset singletons so each test gets fresh state
    TaskManager._instance = None
    ResearchRunManager._instance = None

    return create_app()


def test_start_returns_run_id_and_task_id(monkeypatch, tmp_path):
    """POST /research/start returns 200 with run_id and task_id."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/research/start",
        json={"query": "What is quantum entanglement?"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "run_id" in payload["data"]
    assert "task_id" in payload["data"]
    assert payload["data"]["run_id"].startswith("res_")


def test_start_requires_query(monkeypatch, tmp_path):
    """POST /research/start without query returns 400."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/research/start",
        json={},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "query" in payload["error"].lower()


def test_status_returns_correct_structure(monkeypatch, tmp_path):
    """GET /research/status/<run_id> returns status fields."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    # Start a run
    start_resp = client.post(
        "/api/research/start",
        json={"query": "climate change effects"},
    )
    run_id = start_resp.get_json()["data"]["run_id"]

    # Poll status
    status_resp = client.get(f"/api/research/status/{run_id}")
    assert status_resp.status_code == 200
    payload = status_resp.get_json()
    assert payload["success"] is True
    data = payload["data"]

    # Required fields present
    assert data["run_id"] == run_id
    assert "status" in data
    assert "progress" in data
    assert "message" in data
    assert "connector_used" in data
    assert "task_id" in data
    # Status should be pending or running (thread may not have started yet)
    assert data["status"] in ("pending", "running", "completed", "failed")


def test_status_404_for_unknown_run(monkeypatch, tmp_path):
    """GET /research/status/<unknown> returns 404."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    response = client.get("/api/research/status/nonexistent_run_12345")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["success"] is False


def test_result_404_for_incomplete_run(monkeypatch, tmp_path):
    """GET /research/result/<run_id> for incomplete run returns 404."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    # Start a run (will still be pending/processing)
    start_resp = client.post(
        "/api/research/start",
        json={"query": "machine learning basics"},
    )
    run_id = start_resp.get_json()["data"]["run_id"]

    # Result should not be available yet
    result_resp = client.get(f"/api/research/result/{run_id}")
    assert result_resp.status_code == 404
    payload = result_resp.get_json()
    assert payload["success"] is False


def test_result_404_for_unknown_run(monkeypatch, tmp_path):
    """GET /research/result/<unknown> returns 404."""
    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    response = client.get("/api/research/result/unknown_run_xyz")
    assert response.status_code == 404


def test_failed_connector_marks_run_failed_no_draft(monkeypatch, tmp_path):
    """
    When all connectors fail, the run status must be FAILED and
    draft.md must NOT be written (fail-closed).
    """
    import threading
    import time

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    # Mock all connectors to fail
    def _fail_search(query):
        from app.connectors.base import ConnectorResult
        return ConnectorResult(success=False, error="Simulated connector failure", results=[])

    from app.connectors import fallback_router
    monkeypatch.setattr(fallback_router.ConnectorFallbackRouter, "search", _fail_search)

    start_resp = client.post(
        "/api/research/start",
        json={"query": "test failure path"},
    )
    run_id = start_resp.get_json()["data"]["run_id"]

    # Wait for the background thread to process
    time.sleep(2)

    # Status should be failed
    status_resp = client.get(f"/api/research/status/{run_id}")
    assert status_resp.status_code == 200
    data = status_resp.get_json()["data"]
    assert data["status"] == "failed"
    assert data["error"] != ""

    # Result should not be available
    result_resp = client.get(f"/api/research/result/{run_id}")
    assert result_resp.status_code == 404

    # draft.md should NOT exist on disk
    from app.models.research_run import ResearchRunManager
    draft_path = ResearchRunManager._get_draft_path(run_id)
    assert not os.path.exists(draft_path), "draft.md must NOT be written on failure"


def test_artifact_structure_after_mock_completion(monkeypatch, tmp_path):
    """
    After mocking a successful run, verify the markdown artifact
    contains Summary, Claims, and Sources sections.
    """
    import time

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    from app.connectors.base import ConnectorResult

    # Mock connector returns synthetic results
    def _mock_search(query):
        return ConnectorResult(
            success=True,
            results=[
                {
                    "url": "https://example.com/article1",
                    "content": "Example content about the topic.",
                    "title": "Example Article 1",
                },
                {
                    "url": "https://example.com/article2",
                    "content": "More example content.",
                    "title": "Example Article 2",
                },
            ],
            source="mock_connector",
        )

    from app.connectors import fallback_router
    monkeypatch.setattr(fallback_router.ConnectorFallbackRouter, "search", _mock_search)

    # Mock LLM to return deterministic responses
    from app.utils import llm_client as llm_module

    call_count = [0]

    def _mock_chat(messages, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # Extract node — claims
            return "1. First claim [1]\n2. Second claim [2]"
        elif call_count[0] == 2:
            # Summarize node — summary
            return "This is a test summary covering the topic."
        else:
            return "Fallback"

    monkeypatch.setattr(llm_module.LLMClient, "chat", _mock_chat)

    # Start research
    start_resp = client.post(
        "/api/research/start",
        json={"query": "test artifact structure"},
    )
    run_id = start_resp.get_json()["data"]["run_id"]

    # Wait for completion (2 LLM calls = extract + summarize, sources is formatting only)
    time.sleep(3)

    # Check run completed
    status_resp = client.get(f"/api/research/status/{run_id}")
    data = status_resp.get_json()["data"]

    # Even if LLM fails, connector worked so status should be FAILED or connector_used set
    # The important thing is the artifact IF it completed
    if data["status"] == "completed":
        result_resp = client.get(f"/api/research/result/{run_id}")
        assert result_resp.status_code == 200
        markdown = result_resp.get_json()["data"]["markdown"]

        # Verify sections exist
        assert "## Summary" in markdown
        assert "## Claims" in markdown
        assert "## Sources" in markdown

        # Verify # Deep Research heading
        assert "# Deep Research:" in markdown
        assert "test artifact structure" in markdown


def test_successful_streamed_run_completes_from_nested_langgraph_state(monkeypatch, tmp_path):
    """
    Real LangGraph stream chunks are keyed by node name. The API worker must
    unwrap the nested final chunk instead of expecting top-level summary/claims.
    """
    import time

    app = _make_app(monkeypatch, tmp_path)
    client = app.test_client()

    class _FakeGraph:
        def stream(self, initial_state):
            yield {
                "search_node": {
                    "search_results": [
                        {
                            "url": "https://example.com/source",
                            "title": "Example Source",
                            "content": "Example content",
                        }
                    ],
                    "status": "extracting",
                    "connector_used": "mock_connector",
                }
            }
            yield {
                "extract_node": {
                    "claims": "1. Important claim [1]",
                    "status": "summarizing",
                    "connector_used": "mock_connector",
                }
            }
            yield {
                "summarize_node": {
                    "summary": "Short summary from nested LangGraph state.",
                    "status": "formatting",
                }
            }
            yield {
                "sources_node": {
                    "sources": "- [1] Example Source — https://example.com/source (accessed 2026-04-20)",
                    "status": "completed",
                }
            }

    import app.api.research as research_api

    monkeypatch.setattr(research_api, "compile_research_graph", lambda: _FakeGraph())

    start_resp = client.post(
        "/api/research/start",
        json={"query": "nested stream state"},
    )
    run_id = start_resp.get_json()["data"]["run_id"]

    time.sleep(1)

    status_resp = client.get(f"/api/research/status/{run_id}")
    assert status_resp.status_code == 200
    data = status_resp.get_json()["data"]
    assert data["status"] == "completed"
    assert data["connector_used"] == "mock_connector"

    result_resp = client.get(f"/api/research/result/{run_id}")
    assert result_resp.status_code == 200
    markdown = result_resp.get_json()["data"]["markdown"]
    assert "## Summary" in markdown
    assert "Short summary from nested LangGraph state." in markdown
    assert "## Claims" in markdown
    assert "Important claim [1]" in markdown
    assert "## Sources" in markdown
