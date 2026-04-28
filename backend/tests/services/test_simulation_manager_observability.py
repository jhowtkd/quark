"""Tests for SimulationManager observability integration."""
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


class TestSimulationManagerObservability:
    """Verify SimulationManager emits traces when observability is enabled."""

    def test_init_accepts_observability_client_kwarg(self):
        """SimulationManager.__init__ accepts optional observability_client kwarg."""
        from app.services.simulation_manager import SimulationManager

        fake_obs = _FakeObservabilityClient()
        svc = SimulationManager(observability_client=fake_obs)
        assert svc.observability_client is fake_obs

    def test_init_defaults_to_noop_client(self):
        """SimulationManager.__init__ works without observability_client (default None)."""
        from app.services.simulation_manager import SimulationManager

        svc = SimulationManager()
        # Should default to None (no crash)
        assert svc.observability_client is None

    def test_create_simulation_accepts_observation_parameter(self):
        """create_simulation accepts optional observation parameter."""
        from app.services.simulation_manager import SimulationManager
        import inspect

        sig = inspect.signature(SimulationManager.create_simulation)
        params = list(sig.parameters.keys())
        assert "observation" in params, f"create_simulation should accept observation param, has: {params}"

    def test_create_simulation_with_noop_creates_span(self):
        """create_simulation with NoOpObservabilityClient does not crash."""
        from app.services.simulation_manager import SimulationManager

        noop = NoOpObservabilityClient()
        svc = SimulationManager(observability_client=noop)
        # Should not raise
        state = svc.create_simulation(
            project_id="test-project",
            graph_id="test-graph",
            enable_twitter=True,
            enable_reddit=False,
        )
        assert state.project_id == "test-project"
        assert state.graph_id == "test-graph"

    def test_create_simulation_with_fake_obs_traces(self):
        """create_simulation with fake obs client creates a span."""
        from app.services.simulation_manager import SimulationManager

        fake_obs = _FakeObservabilityClient()
        svc = SimulationManager(observability_client=fake_obs)

        # Create root span as parent
        root = fake_obs.start_report_trace(
            name="test_trace",
            session_id="test-session",
        )

        state = svc.create_simulation(
            project_id="proj-1",
            graph_id="graph-1",
            enable_twitter=True,
            enable_reddit=True,
            observation=root,
        )

        assert state.simulation_id is not None
        # Check that child span was created
        child_spans = root.child_spans
        assert len(child_spans) >= 1
        create_span = next((s for s in child_spans if "create_simulation" in s.name), None)
        assert create_span is not None, f"Expected create_simulation span, got: {[s.name for s in child_spans]}"
        assert create_span._ended is True, "Span should be ended"

    def test_prepare_simulation_accepts_observation_parameter(self):
        """prepare_simulation accepts optional observation parameter."""
        from app.services.simulation_manager import SimulationManager
        import inspect

        sig = inspect.signature(SimulationManager.prepare_simulation)
        params = list(sig.parameters.keys())
        assert "observation" in params
