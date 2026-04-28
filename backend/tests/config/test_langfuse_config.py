"""Tests for Langfuse observability configuration."""

import pytest


class TestLangfuseConfig:
    """LANGFUSE_* settings and validation behavior."""

    def test_langfuse_disabled_does_not_require_credentials(self, monkeypatch):
        """When LANGFUSE_ENABLED=false, no credentials are demanded."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "false")
        monkeypatch.delenv("LANGFUSE_HOST", raising=False)
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        from app.config import Config

        errors = Config.validate()

        langfuse_errors = [e for e in errors if "LANGFUSE" in e]
        assert langfuse_errors == [], f"unexpected langfuse errors: {langfuse_errors}"

    def test_langfuse_enabled_requires_host_and_keys(self, monkeypatch):
        """When LANGFUSE_ENABLED=true, host and credentials are required."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "true")
        monkeypatch.delenv("LANGFUSE_HOST", raising=False)
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        from app.config import Config

        errors = Config.validate()

        assert any("LANGFUSE_HOST" in e for e in errors), "missing LANGFUSE_HOST error"
        assert any("LANGFUSE_PUBLIC_KEY" in e for e in errors), "missing LANGFUSE_PUBLIC_KEY error"
        assert any("LANGFUSE_SECRET_KEY" in e for e in errors), "missing LANGFUSE_SECRET_KEY error"

    def test_langfuse_disabled_skips_host_validation(self, monkeypatch):
        """Enabled=false should not care about host value at all."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "false")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        from app.config import Config

        errors = Config.validate()

        langfuse_errors = [e for e in errors if "LANGFUSE" in e]
        assert langfuse_errors == [], f"unexpected langfuse errors: {langfuse_errors}"
