"""Tests for SimulationRunner observability integration."""
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


class TestSimulationRunnerObservability:
    """Verify SimulationRunner emits traces when observability is enabled."""

    def test_start_simulation_accepts_observation_parameter(self):
        """start_simulation accepts optional observation parameter."""
        from app.services.simulation_runner import SimulationRunner
        import inspect

        sig = inspect.signature(SimulationRunner.start_simulation)
        params = list(sig.parameters.keys())
        assert "observation" in params, f"start_simulation should accept observation, has: {params}"

    def test_stop_simulation_accepts_observation_parameter(self):
        """stop_simulation accepts optional observation parameter."""
        from app.services.simulation_runner import SimulationRunner
        import inspect

        sig = inspect.signature(SimulationRunner.stop_simulation)
        params = list(sig.parameters.keys())
        assert "observation" in params, f"stop_simulation should accept observation, has: {params}"

    def test_start_simulation_with_nonexistent_config_raises(self):
        """start_simulation with nonexistent simulation raises ValueError (observation doesn't break)."""
        from app.services.simulation_runner import SimulationRunner
        import os

        # Use a temp dir that definitely won't have a config
        SimulationRunner.RUN_STATE_DIR = "/tmp/nonexistent_sim_dir"
        SimulationRunner.SCRIPTS_DIR = "/tmp/nonexistent_scripts_dir"

        fake_obs = _FakeObservabilityClient()
        root = fake_obs.start_report_trace(name="test", session_id="test-session")

        try:
            SimulationRunner.start_simulation(
                simulation_id="nonexistent",
                observation=root,
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "模拟配置不存在" in str(e) or "not found" in str(e).lower()
            assert len(root.child_spans) == 1
            span = root.child_spans[0]
            assert span.name == "simulation_runner.start_simulation"
            assert span._ended is True
        finally:
            SimulationRunner.RUN_STATE_DIR = os.path.join(
                os.path.dirname(__file__), "../../uploads/simulations"
            )
            SimulationRunner.SCRIPTS_DIR = os.path.join(
                os.path.dirname(__file__), "../../scripts"
            )

    def test_stop_simulation_with_nonexistent_sim_raises(self):
        """stop_simulation with nonexistent simulation raises ValueError (observation doesn't break)."""
        from app.services.simulation_runner import SimulationRunner

        fake_obs = _FakeObservabilityClient()
        root = fake_obs.start_report_trace(name="test", session_id="test-session")

        try:
            SimulationRunner.stop_simulation(
                simulation_id="definitely-nonexistent-sim-id-12345",
                observation=root,
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            assert len(root.child_spans) == 1
            span = root.child_spans[0]
            assert span.name == "simulation_runner.stop_simulation"
            assert span._ended is True

    def test_stop_simulation_already_stopped_returns_without_error(self):
        """stop_simulation when simulation already stopped returns without error."""
        from app.services.simulation_runner import SimulationRunner, RunnerStatus, SimulationRunState

        # Inject a completed state so it's already stopped
        completed_state = SimulationRunState(
            simulation_id="already-stopped-test",
            runner_status=RunnerStatus.COMPLETED,
            started_at="2025-01-01T00:00:00",
            completed_at="2025-01-01T01:00:00",
        )
        SimulationRunner._run_states["already-stopped-test"] = completed_state

        try:
            result = SimulationRunner.stop_simulation(
                simulation_id="already-stopped-test",
            )
            # Should return without raising
            assert result.runner_status == RunnerStatus.COMPLETED
        finally:
            SimulationRunner._run_states.pop("already-stopped-test", None)
