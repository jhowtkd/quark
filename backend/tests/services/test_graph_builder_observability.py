"""Tests for GraphBuilderService observability integration."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.observability.langfuse_client import NoOpObservabilityClient


class _FakeSpan:
    """Minimal fake Langfuse span."""

    def __init__(self, name: str = "test", **kwargs):
        self.name = name
        self.kwargs = kwargs
        self.updates = []
        self._ended = False
        self.child_spans = []

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self

    def end(self):
        self._ended = True

    def start_span(self, name: str, **kw):
        child = _FakeSpan(name, **kw)
        self.child_spans.append(child)
        return child


class _FakeObservabilityClient:
    """Minimal fake Langfuse client."""

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


class TestGraphBuilderObservability:
    """Verify GraphBuilderService emits traces when observability is enabled."""

    def test_init_accepts_observability_client_parameter(self):
        """GraphBuilderService.__init__ accepts optional observability_client kwarg."""
        from app.services.graph_builder import GraphBuilderService
        import app.services.graph_builder as gb
        import os

        original_key = gb.Config.ZEP_API_KEY
        gb.Config.ZEP_API_KEY = "test-key"
        try:
            fake_obs = _FakeObservabilityClient()
            svc = GraphBuilderService(observability_client=fake_obs)
            assert svc.observability_client is fake_obs
        finally:
            gb.Config.ZEP_API_KEY = original_key

    def test_build_graph_async_accepts_observation_parameter(self):
        """build_graph_async accepts an optional observation parameter."""
        from app.services.graph_builder import GraphBuilderService
        import inspect

        sig = inspect.signature(GraphBuilderService.build_graph_async)
        assert "observation" in sig.parameters, \
            f"build_graph_async should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_build_graph_async_with_noop_client(self):
        """GraphBuilderService works with NoOpObservabilityClient."""
        from app.services.graph_builder import GraphBuilderService
        import app.services.graph_builder as gb

        original_key = gb.Config.ZEP_API_KEY
        gb.Config.ZEP_API_KEY = "test-key"
        try:
            noop = NoOpObservabilityClient()
            svc = GraphBuilderService(observability_client=noop)
            assert svc.observability_client is noop
        finally:
            gb.Config.ZEP_API_KEY = original_key

    def test_build_graph_async_with_fake_obs_traces(self):
        """build_graph_async with fake obs creates and ends a span."""
        from app.services.graph_builder import GraphBuilderService
        import app.services.graph_builder as gb

        original_key = gb.Config.ZEP_API_KEY
        gb.Config.ZEP_API_KEY = "test-key"
        try:
            fake_obs = _FakeObservabilityClient()
            svc = GraphBuilderService(observability_client=fake_obs)

            root = fake_obs.start_report_trace(name="test", session_id="test-session")

            # Build a minimal ontology
            ontology = {"Person": {"type": "entity", "attributes": ["name", "role"]}}

            task_id = svc.build_graph_async(
                text="John is a developer who works at FuturIA.",
                ontology=ontology,
                graph_name="Test Graph",
                observation=root,
            )

            assert task_id is not None
            child_spans = root.child_spans
            assert len(child_spans) >= 1
            gb_span = next((s for s in child_spans if "build_graph_async" in s.name), None)
            assert gb_span is not None, f"Expected build_graph_async span, got: {[s.name for s in child_spans]}"
            assert gb_span._ended is True, "Span should be ended"
        finally:
            gb.Config.ZEP_API_KEY = original_key
