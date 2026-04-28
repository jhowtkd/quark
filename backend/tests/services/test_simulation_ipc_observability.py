"""Tests for SimulationIPCClient observability integration."""
import pytest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.observability.langfuse_client import NoOpObservabilityClient
from app.services.simulation_ipc import SimulationIPCClient, CommandType


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


class TestSimulationIPCObservability:
    """Verify SimulationIPCClient emits traces when observability is enabled."""

    def test_init_accepts_observability_client_parameter(self):
        """SimulationIPCClient.__init__ accepts optional observability_client kwarg."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_obs = _FakeObservabilityClient()
            client = SimulationIPCClient(simulation_dir=tmpdir, observability_client=fake_obs)
            assert client.observability_client is fake_obs

    def test_send_command_accepts_observation_parameter(self):
        """send_command accepts an optional observation parameter."""
        from app.services.simulation_ipc import SimulationIPCClient
        import inspect

        sig = inspect.signature(SimulationIPCClient.send_command)
        assert "observation" in sig.parameters, \
            f"send_command should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_ipc_with_noop_client(self):
        """SimulationIPCClient works with NoOpObservabilityClient."""
        with tempfile.TemporaryDirectory() as tmpdir:
            noop = NoOpObservabilityClient()
            client = SimulationIPCClient(simulation_dir=tmpdir, observability_client=noop)
            assert client.observability_client is noop
            assert client.observability_client.is_enabled is False
