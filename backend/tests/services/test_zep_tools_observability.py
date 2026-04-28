"""Tests for ZepToolsService observability integration."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.observability.langfuse_client import NoOpObservabilityClient


class _FakeSpan:
    """Minimal fake Langfuse span."""

    def __init__(self, name: str = "test", **kwargs):
        self.name = name
        self.initial_kwargs = kwargs
        self.updates = []
        self._ended = False
        self.child_spans = []

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self

    def end(self):
        self._ended = True

    def start_span(self, name: str, **kwargs):
        child = _FakeSpan(name, **kwargs)
        self.child_spans.append(child)
        return child

    def score(self, **kwargs):
        return None

    def score_trace(self, **kwargs):
        return None


class _FakeObservabilityClient:
    """Minimal fake Langfuse client matching LangfuseObservabilityClient interface."""

    def __init__(self):
        self.spans = []

    def start_report_trace(self, name: str, session_id: str = "", metadata: dict | None = None):
        span = _FakeSpan(name, session_id=session_id, metadata=metadata or {})
        self.spans.append(span)
        return span

    def start_span(self, name: str, metadata: dict | None = None):
        return _FakeSpan(name, metadata=metadata or {})

    def flush(self):
        return None

    def shutdown(self):
        return None


class TestZepToolsObservability:
    """Verify ZepToolsService emits traces when observability is enabled."""

    def test_init_accepts_observability_client_parameter(self):
        """ZepToolsService.__init__ accepts optional observability_client kwarg."""
        from app.services.zep_tools import ZepToolsService

        fake_obs = _FakeObservabilityClient()
        # This will raise ZEP_API_KEY not configured, so mock it
        import app.services.zep_tools as zt
        original_key = zt.Config.ZEP_API_KEY
        zt.Config.ZEP_API_KEY = "test-key"
        try:
            svc = ZepToolsService(observability_client=fake_obs)
            assert svc.observability_client is fake_obs
        finally:
            zt.Config.ZEP_API_KEY = original_key

    def test_insight_forge_accepts_observation_parameter(self):
        """insight_forge accepts an optional observation parameter."""
        from app.services.zep_tools import ZepToolsService
        import inspect

        sig = inspect.signature(ZepToolsService.insight_forge)
        assert "observation" in sig.parameters, \
            f"insight_forge should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_generate_sub_queries_accepts_observation_parameter(self):
        """_generate_sub_queries accepts an optional observation parameter."""
        from app.services.zep_tools import ZepToolsService
        import inspect

        sig = inspect.signature(ZepToolsService._generate_sub_queries)
        assert "observation" in sig.parameters, \
            f"_generate_sub_queries should accept 'observation' param"

    def test_zep_tools_with_noop_client(self):
        """ZepToolsService can be instantiated with NoOpObservabilityClient."""
        from app.services.zep_tools import ZepToolsService
        import app.services.zep_tools as zt

        original_key = zt.Config.ZEP_API_KEY
        zt.Config.ZEP_API_KEY = "test-key"
        try:
            noop = NoOpObservabilityClient()
            svc = ZepToolsService(observability_client=noop)
            assert svc.observability_client is noop
            assert svc.observability_client.is_enabled is False
        finally:
            zt.Config.ZEP_API_KEY = original_key
