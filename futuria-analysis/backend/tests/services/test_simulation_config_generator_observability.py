"""Tests for SimulationConfigGenerator observability integration.

Verifies that SimulationConfigGenerator.generate_config() creates root traces and
child spans when an observability client is supplied.
"""
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
    """Minimal fake Langfuse client matching the LangfuseObservabilityClient interface."""

    def __init__(self):
        self.spans = []

    def start_report_trace(self, name: str, session_id: str = "", metadata: dict | None = None):
        span = _FakeSpan(name, session_id=session_id, metadata=metadata or {})
        self.spans.append(span)
        return span

    def flush(self):
        return None

    def shutdown(self):
        return None


class TestSimulationConfigGeneratorTracing:
    """Verify SimulationConfigGenerator emits traces when observability is enabled."""

    def test_init_accepts_observability_client_parameter(self):
        """SimulationConfigGenerator.__init__ accepts an optional observability_client kwarg."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        fake_obs = _FakeObservabilityClient()
        gen = SimulationConfigGenerator(
            api_key="test-key",
            observability_client=fake_obs,
        )
        assert gen.observability_client is fake_obs

    def test_init_defaults_to_noop_observability_client(self):
        """When no observability_client is passed, it defaults to None."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        gen = SimulationConfigGenerator(api_key="test-key")
        assert gen.observability_client is None

    def test_generate_config_accepts_observability_client_parameter(self):
        """generate_config accepts an optional observability_client parameter."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        gen = SimulationConfigGenerator(api_key="test-key")
        sig_params = list(gen.generate_config.__code__.co_varnames)
        assert "observability_client" in sig_params, \
            f"generate_config should accept observability_client, has: {sig_params}"

    def test_generate_config_creates_root_trace_when_obs_client_provided(self):
        """When generate_config has an obs client, it creates a root simulation_config trace."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        fake_obs = _FakeObservabilityClient()
        gen = SimulationConfigGenerator(
            api_key="test-key",
            observability_client=fake_obs,
        )

        # Patch the entity class used in generate_config
        from app.services.simulation_config_generator import EntityNode

        class FakeEntity:
            def __init__(self, uuid_val, name, etype):
                self.uuid = uuid_val
                self.name = name
                self._etype = etype

            def get_entity_type(self):
                return self._etype

            summary = "fake summary"

        entities = [
            FakeEntity(uuid_val=f"u{i}", name=f"Entity {i}", etype="Student")
            for i in range(3)
        ]

        # Patch the LLM call to return valid config
        import app.services.simulation_config_generator as scg

        original_call = gen._call_llm_with_retry

        def fake_llm(prompt, system, observation=None):
            if observation is not None:
                observation.update(output={"time_config": "ok"}, latency_ms=50.0)
                observation.end()
            return {
                "total_simulation_hours": 72,
                "minutes_per_round": 60,
                "agents_per_hour_min": 1,
                "agents_per_hour_max": 5,
                "peak_hours": [19, 20, 21, 22],
                "off_peak_hours": [0, 1, 2, 3, 4, 5],
                "morning_hours": [6, 7, 8],
                "work_hours": list(range(9, 19)),
                "reasoning": "fake reasoning",
            }

        gen._call_llm_with_retry = fake_llm

        # Also need to patch the event config and agent config LLM calls
        def fake_llm_event(prompt, system, observation=None):
            if observation is not None:
                observation.update(output={"event": "ok"}, latency_ms=30.0)
                observation.end()
            return {
                "hot_topics": ["topic1"],
                "narrative_direction": "direction",
                "initial_posts": [],
                "reasoning": "fake",
            }

        def fake_llm_agents(prompt, system, observation=None):
            if observation is not None:
                observation.update(output={"agents": "ok"}, latency_ms=40.0)
                observation.end()
            return {"agent_configs": []}

        gen._generate_event_config = lambda *a, **kw: fake_llm_event("", "")
        gen._generate_agent_configs_batch = lambda *a, **kw: []

        try:
            result = gen.generate_config(
                simulation_id="sim-obs-test",
                project_id="proj-1",
                graph_id="graph-1",
                simulation_requirement="test simulation",
                document_text="test document",
                entities=entities,
                enable_twitter=True,
                enable_reddit=False,
                observability_client=fake_obs,
            )

            # Should have created a root span
            assert len(fake_obs.spans) >= 1, f"Expected at least 1 span, got {len(fake_obs.spans)}"
            root_span = fake_obs.spans[0]
            assert root_span.name == "simulation_config", f"Expected 'simulation_config', got '{root_span.name}'"
            assert root_span._ended is True, "Root span should be ended after generate_config completes"
        finally:
            gen._call_llm_with_retry = original_call

    def test_generate_time_config_accepts_observation_parameter(self):
        """_generate_time_config accepts an optional observation parameter."""
        from app.services.simulation_config_generator import SimulationConfigGenerator
        import inspect

        sig = inspect.signature(SimulationConfigGenerator._generate_time_config)
        assert "observation" in sig.parameters, \
            f"_generate_time_config should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_generate_event_config_accepts_observation_parameter(self):
        """_generate_event_config accepts an optional observation parameter."""
        from app.services.simulation_config_generator import SimulationConfigGenerator
        import inspect

        sig = inspect.signature(SimulationConfigGenerator._generate_event_config)
        assert "observation" in sig.parameters, \
            f"_generate_event_config should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_generate_agent_configs_batch_accepts_observation_parameter(self):
        """_generate_agent_configs_batch accepts an optional observation parameter."""
        from app.services.simulation_config_generator import SimulationConfigGenerator
        import inspect

        sig = inspect.signature(SimulationConfigGenerator._generate_agent_configs_batch)
        assert "observation" in sig.parameters, \
            f"_generate_agent_configs_batch should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_call_llm_with_retry_accepts_observation_parameter(self):
        """_call_llm_with_retry accepts an optional observation parameter."""
        from app.services.simulation_config_generator import SimulationConfigGenerator
        import inspect

        sig = inspect.signature(SimulationConfigGenerator._call_llm_with_retry)
        assert "observation" in sig.parameters, \
            f"_call_llm_with_retry should accept 'observation' param, has: {list(sig.parameters.keys())}"

    def test_generate_without_obs_client_does_not_crash(self):
        """When no obs client is set, generate_config works exactly as before."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        gen = SimulationConfigGenerator(api_key="test-key")
        assert gen.observability_client is None

        # Patch LLM call
        def fake_llm(prompt, system, observation=None):
            return {
                "total_simulation_hours": 72,
                "minutes_per_round": 60,
                "agents_per_hour_min": 1,
                "agents_per_hour_max": 5,
                "peak_hours": [19, 20, 21, 22],
                "off_peak_hours": [0, 1, 2, 3, 4, 5],
                "morning_hours": [6, 7, 8],
                "work_hours": list(range(9, 19)),
                "reasoning": "fake",
            }

        gen._call_llm_with_retry = fake_llm
        gen._generate_event_config = lambda *a, **kw: {
            "hot_topics": [], "narrative_direction": "", "initial_posts": [], "reasoning": "fake"
        }
        gen._generate_agent_configs_batch = lambda *a, **kw: []

        class FakeEntity:
            def __init__(self, uuid_val, name, etype):
                self.uuid = uuid_val
                self.name = name
                self._etype = etype

            def get_entity_type(self):
                return self._etype

            summary = "fake"

        entities = [FakeEntity(f"u{i}", f"E{i}", "Student") for i in range(2)]

        result = gen.generate_config(
            simulation_id="no-obs-test",
            project_id="proj-1",
            graph_id="graph-1",
            simulation_requirement="test",
            document_text="doc",
            entities=entities,
            enable_twitter=True,
            enable_reddit=False,
        )
        assert result is not None
        assert result.simulation_id == "no-obs-test"


class TestNoOpClientWithSimulationConfig:
    """Verify NoOpObservabilityClient works with SimulationConfigGenerator."""

    def test_simulation_config_generator_with_noop_client(self):
        """SimulationConfigGenerator can be instantiated with NoOpObservabilityClient."""
        from app.services.simulation_config_generator import SimulationConfigGenerator

        noop = NoOpObservabilityClient()
        gen = SimulationConfigGenerator(
            api_key="test-key",
            observability_client=noop,
        )
        assert gen.observability_client is noop
        assert gen.observability_client.is_enabled is False
