"""Tests for observability lifecycle wiring in the Flask application factory."""

import pytest


def test_app_exposes_observability_client_in_config(monkeypatch):
    """The Flask app config must expose one shared observability client."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app
    from app.config import Config

    app = create_app()

    assert "OBSERVABILITY_CLIENT" in app.config
    assert hasattr(app.config["OBSERVABILITY_CLIENT"], "is_enabled")
    assert hasattr(app.config["OBSERVABILITY_CLIENT"], "start_report_trace")
    assert hasattr(app.config["OBSERVABILITY_CLIENT"], "flush")
    assert hasattr(app.config["OBSERVABILITY_CLIENT"], "shutdown")


def test_health_endpoint_still_works(monkeypatch):
    """Health endpoint must return ok with observability wired in."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app

    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "FUTUR.IA Backend"


def test_disabled_observability_client_is_noop(monkeypatch):
    """With LANGFUSE_ENABLED=false, the app client must be a no-op."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app

    app = create_app()
    obs_client = app.config["OBSERVABILITY_CLIENT"]

    assert obs_client.is_enabled is False
    obs = obs_client.start_report_trace(name="test", session_id="s1", metadata={})
    assert obs.is_noop is True


def test_blueprints_still_registered(monkeypatch):
    """All existing blueprints must still be registered with observability wired."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")

    from app import create_app

    app = create_app()

    # Check registered rules (url_map is the Werkzeug URL map)
    rule_names = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "report.get_report" in rule_names or any("report" in r for r in rule_names)
