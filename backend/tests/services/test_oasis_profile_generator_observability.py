"""Tests for OasisProfileGenerator observability integration.

Verifies that OasisProfileGenerator creates profile generation spans
when an observability client is supplied.
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

    def start_span(self, name: str, metadata: dict | None = None):
        return _FakeSpan(name, metadata=metadata or {})

    def flush(self):
        return None

    def shutdown(self):
        return None


class TestOasisProfileGeneratorTracing:
    """Verify OasisProfileGenerator emits profile generation spans."""

    def test_init_accepts_observability_client_parameter(self):
        """OasisProfileGenerator.__init__ accepts optional observability_client kwarg."""
        from app.services.oasis_profile_generator import OasisProfileGenerator

        fake_obs = _FakeObservabilityClient()
        gen = OasisProfileGenerator(
            api_key="test-key",
            observability_client=fake_obs,
        )
        assert gen.observability_client is fake_obs

    def test_init_defaults_to_noop_observability_client(self):
        """When no observability_client is passed, it defaults to None."""
        from app.services.oasis_profile_generator import OasisProfileGenerator

        gen = OasisProfileGenerator(api_key="test-key")
        assert gen.observability_client is None

    def test_generate_profile_from_entity_accepts_observation_parameter(self):
        """generate_profile_from_entity accepts an optional observation parameter."""
        from app.services.oasis_profile_generator import OasisProfileGenerator
        import inspect

        sig = inspect.signature(OasisProfileGenerator.generate_profile_from_entity)
        assert "observation" in sig.parameters, \
            f"generate_profile_from_entity should accept 'observation' param"

    def test_generate_profiles_from_entities_accepts_observation_parameter(self):
        """generate_profiles_from_entities accepts an optional observation parameter."""
        from app.services.oasis_profile_generator import OasisProfileGenerator
        import inspect

        sig = inspect.signature(OasisProfileGenerator.generate_profiles_from_entities)
        assert "observation" in sig.parameters, \
            f"generate_profiles_from_entities should accept 'observation' param"

    def test_generate_profile_from_entity_creates_span_when_obs_provided(self):
        """When observation is provided, generate_profile_from_entity creates a span."""
        from app.services.oasis_profile_generator import OasisProfileGenerator

        fake_obs = _FakeObservabilityClient()
        gen = OasisProfileGenerator(
            api_key="test-key",
            observability_client=fake_obs,
        )

        # Create a parent span like the batch method would
        parent_span = fake_obs.start_report_trace(
            name="profile_batch",
            session_id="test-sim",
        )

        # Create a fake entity
        from app.services.zep_entity_reader import EntityNode

        class FakeEntity:
            def __init__(self):
                self.uuid = "entity-uuid-1"
                self.name = "Student Alice"
                self.summary = "A student interested in technology"

                self.attributes = {}
                self.related_edges = []
                self.related_nodes = []

            def get_entity_type(self):
                return "student"

        entity = FakeEntity()

        # Patch _generate_profile_with_llm to avoid real LLM call
        original_llm = gen._generate_profile_with_llm

        def fake_llm(**kw):
            return {
                "bio": "A student bio",
                "persona": "A student persona",
                "age": 22,
                "gender": "female",
                "mbti": "INTP",
                "country": "China",
                "profession": "Student",
                "interested_topics": ["tech", "science"],
            }

        gen._generate_profile_with_llm = fake_llm

        try:
            result = gen.generate_profile_from_entity(
                entity=entity,
                user_id=1,
                use_llm=True,
                observation=parent_span,
            )
            # Should have created a child span
            assert len(parent_span.child_spans) == 1, \
                f"Expected 1 child span, got {len(parent_span.child_spans)}"
            child_span = parent_span.child_spans[0]
            assert child_span.name == "profile_generation"
            assert child_span._ended is True, "Child span should be ended"
        finally:
            gen._generate_profile_with_llm = original_llm

    def test_generate_profile_from_entity_records_retry_attempt_spans(self, monkeypatch):
        """Retry loop should emit attempt spans under profile_generation."""
        from app.services.oasis_profile_generator import OasisProfileGenerator
        import json

        fake_obs = _FakeObservabilityClient()
        gen = OasisProfileGenerator(
            api_key="test-key",
            observability_client=fake_obs,
        )

        parent_span = fake_obs.start_report_trace(
            name="profile_batch",
            session_id="test-sim",
        )

        class FakeEntity:
            def __init__(self):
                self.uuid = "entity-uuid-2"
                self.name = "Student Bob"
                self.summary = "A student interested in media and technology"
                self.attributes = {}
                self.related_edges = []
                self.related_nodes = []

            def get_entity_type(self):
                return "student"

        class FakeUsage:
            prompt_tokens = 11
            completion_tokens = 19
            total_tokens = 30

        class FakeResponse:
            def __init__(self, content: str):
                self.choices = [type("Choice", (), {
                    "message": type("Msg", (), {"content": content})(),
                    "finish_reason": "stop",
                })()]
                self.usage = FakeUsage()

        attempts = {"count": 0}

        def fake_create(**kwargs):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("temporary profile failure")

            return FakeResponse(json.dumps({
                "bio": "A recovered student bio",
                "persona": "A recovered student persona",
                "age": 21,
                "gender": "male",
                "mbti": "INTP",
                "country": "US",
                "profession": "Student",
                "interested_topics": ["tech", "news"],
            }))

        monkeypatch.setattr(gen.client.chat.completions, "create", fake_create)
        monkeypatch.setattr("app.services.oasis_profile_generator.time.sleep", lambda *args, **kwargs: None)

        result = gen.generate_profile_from_entity(
            entity=FakeEntity(),
            user_id=2,
            use_llm=True,
            observation=parent_span,
        )

        assert result is not None
        assert len(parent_span.child_spans) == 1
        entity_span = parent_span.child_spans[0]
        assert entity_span.name == "profile_generation"
        assert len(entity_span.child_spans) == 2
        assert [span.name for span in entity_span.child_spans] == [
            "profile_generation.attempt",
            "profile_generation.attempt",
        ]
        assert all(span._ended for span in entity_span.child_spans)

    def test_generate_without_obs_client_does_not_crash(self):
        """When no obs client is set, generate_profile_from_entity works as before."""
        from app.services.oasis_profile_generator import OasisProfileGenerator

        gen = OasisProfileGenerator(api_key="test-key")
        assert gen.observability_client is None

        class FakeEntity:
            def __init__(self):
                self.uuid = "u1"
                self.name = "Test Entity"
                self.summary = "Test summary"

                self.attributes = {}
                self.related_edges = []
                self.related_nodes = []

            def get_entity_type(self):
                return "student"

        entity = FakeEntity()

        original_llm = gen._generate_profile_with_llm

        def fake_llm(**kw):
            return {
                "bio": "Bio",
                "persona": "Persona",
                "age": 20,
                "gender": "male",
                "mbti": "INTJ",
                "country": "US",
                "profession": "Student",
                "interested_topics": [],
            }

        gen._generate_profile_with_llm = fake_llm

        try:
            result = gen.generate_profile_from_entity(
                entity=entity,
                user_id=0,
                use_llm=True,
                # No observation passed
            )
            assert result is not None
            assert result.user_id == 0
        finally:
            gen._generate_profile_from_entity = original_llm


class TestNoOpClientWithOasisProfileGenerator:
    """Verify NoOpObservabilityClient works with OasisProfileGenerator."""

    def test_oasis_profile_generator_with_noop_client(self):
        """OasisProfileGenerator can be instantiated with NoOpObservabilityClient."""
        from app.services.oasis_profile_generator import OasisProfileGenerator

        noop = NoOpObservabilityClient()
        gen = OasisProfileGenerator(
            api_key="test-key",
            observability_client=noop,
        )
        assert gen.observability_client is noop
        assert gen.observability_client.is_enabled is False
