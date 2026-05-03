"""Tests for Langfuse beta sampling restrictions."""

import importlib
import pytest


class TestLangfuseBetaRestriction:
    """LANGFUSE_SAMPLE_RATE must be <= 0.2 in beta environments."""

    def _reload_config(self):
        """Reload config module so class variables pick up current env."""
        import app.config as config_module
        importlib.reload(config_module)
        return config_module.Config

    def test_beta_env_rejects_high_sample_rate(self, monkeypatch):
        """When LANGFUSE_ENABLED=true, LANGFUSE_ENV=beta, and sample rate > 0.2,
        validation returns an error containing 'sample rate'."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "true")
        monkeypatch.setenv("LANGFUSE_ENV", "beta")
        monkeypatch.setenv("LANGFUSE_SAMPLE_RATE", "0.5")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        Config = self._reload_config()
        errors = Config.validate()

        sample_rate_errors = [e for e in errors if "sample rate" in e.lower() or "sample_rate" in e.lower()]
        assert sample_rate_errors, f"expected 'sample rate' error, got: {errors}"

    def test_beta_env_accepts_low_sample_rate(self, monkeypatch):
        """When LANGFUSE_ENABLED=true, LANGFUSE_ENV=beta, and sample rate <= 0.2,
        validation passes without sample-rate errors."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "true")
        monkeypatch.setenv("LANGFUSE_ENV", "beta")
        monkeypatch.setenv("LANGFUSE_SAMPLE_RATE", "0.1")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        Config = self._reload_config()
        errors = Config.validate()

        sample_rate_errors = [e for e in errors if "sample rate" in e.lower() or "sample_rate" in e.lower()]
        assert sample_rate_errors == [], f"unexpected sample rate errors: {sample_rate_errors}"

    def test_beta_env_boundary_0_2_is_accepted(self, monkeypatch):
        """Exactly 0.2 is accepted in beta."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "true")
        monkeypatch.setenv("LANGFUSE_ENV", "beta")
        monkeypatch.setenv("LANGFUSE_SAMPLE_RATE", "0.2")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        Config = self._reload_config()
        errors = Config.validate()

        sample_rate_errors = [e for e in errors if "sample rate" in e.lower() or "sample_rate" in e.lower()]
        assert sample_rate_errors == [], f"unexpected sample rate errors: {sample_rate_errors}"

    def test_non_beta_env_ignores_sample_rate(self, monkeypatch):
        """Non-beta environments are not restricted by sample rate."""
        monkeypatch.setenv("LANGFUSE_ENABLED", "true")
        monkeypatch.setenv("LANGFUSE_ENV", "production")
        monkeypatch.setenv("LANGFUSE_SAMPLE_RATE", "1.0")
        monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        Config = self._reload_config()
        errors = Config.validate()

        sample_rate_errors = [e for e in errors if "sample rate" in e.lower() or "sample_rate" in e.lower()]
        assert sample_rate_errors == [], f"unexpected sample rate errors: {sample_rate_errors}"
