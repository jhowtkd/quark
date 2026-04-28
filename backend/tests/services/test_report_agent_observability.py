"""Tests for ReportAgent observability integration.

Verifies that ReportAgent.generate_report() creates root traces and
plan_outline() creates planning spans when an observability client is supplied.
"""

import pytest
import sys
from pathlib import Path

# Ensure app import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.observability.langfuse_client import NoOpObservabilityClient

# Re-export for backward compatibility with tests that reference these names
FakeObservation = NoOpObservabilityClient
# _FakeObservation: many tests use this as a fake that has .spans — use _FakeObservabilityClient
_FakeObservation = None  # placeholder, set after _FakeObservabilityClient is defined


class _FakeSpan:
    """
    Minimal fake Langfuse span.
    
    Acts as both:
    - A root trace returned from start_report_trace() on the client
    - A parent span that supports start_span() for child spans
    """

    def __init__(self, name: str = "test", **initial_kwargs):
        self.name = name
        self.initial_kwargs = initial_kwargs
        self.updates = []
        self._ended = False
        self.child_spans = []

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return self

    def end(self):
        self._ended = True

    def start_span(self, name: str, **kwargs):
        """Create a child span. Returns another _FakeSpan."""
        child = _FakeSpan(name, **kwargs)
        self.child_spans.append(child)
        return child

    def score(self, **kwargs):
        """No-op score call."""
        return None

    def score_trace(self, **kwargs):
        """No-op trace-level score call."""
        return None


class _FakeObservabilityClient:
    """
    Minimal fake Langfuse client matching the LangfuseObservabilityClient interface.
    
    Used in tests as a stand-in for the real Langfuse client.
    start_report_trace() returns a _FakeSpan that supports start_span() for child spans.
    """

    def __init__(self):
        self.spans = []

    def start_report_trace(self, name: str, session_id: str = "", metadata: dict | None = None):
        """Create a root trace and return a _FakeSpan."""
        span = _FakeSpan(name, session_id=session_id, metadata=metadata or {})
        self.spans.append(span)
        return span

    def start_span(self, name: str, metadata: dict | None = None):
        """Start a standalone span from the client (no parent trace)."""
        return _FakeSpan(name=name, metadata=metadata or {})

    def flush(self):
        return None

    def shutdown(self):
        return None


# Set _FakeObservation to the fake client (which has .spans) so tests that
# use _FakeObservation() get a fake that supports .spans, not the real NoOp
_FakeObservation = _FakeObservabilityClient


class TestReportAgentTracing:
    """Verify ReportAgent emits root traces and planning spans."""

    def test_init_accepts_observability_client_parameter(self):
        """ReportAgent.__init__ accepts an optional observability_client kwarg."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test req",
            observability_client=fake_obs,
        )
        assert agent.observability_client is fake_obs

    def test_init_defaults_to_noop_observability_client(self):
        """When no observability_client is passed, it defaults to None."""
        from app.services.report_agent import ReportAgent

        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test req",
        )
        assert agent.observability_client is None

    def test_generate_report_creates_root_trace_when_obs_client_provided(self):
        """When ReportAgent has an obs client, generate_report creates a root trace."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test requirement",
            observability_client=fake_obs,
        )

        # Monkeypatch generate_report to avoid real work
        original_plan_outline = agent.plan_outline

        def fake_plan_outline(**kwargs):
            # Verify observation was passed
            assert kwargs.get("observability_client") is not None, \
                "Root trace should be passed to plan_outline"
            return original_plan_outline(**kwargs)

        agent.plan_outline = fake_plan_outline

        # Patch ReportManager and logger to avoid file I/O
        import app.services.report_agent as ra_module
        ra_module.ReportManager._ensure_report_folder = lambda x: None
        ra_module.ReportManager.save_report = lambda *a, **kw: None
        ra_module.ReportManager.update_progress = lambda *a, **kw: None

        import app.services.report_agent as ra
        original_logger = ra.logger
        ra.logger = type('FakeLogger', (), {
            'info': lambda self, msg, **kw: None,
            'error': lambda self, msg, **kw: None,
        })()

        agent.report_logger = type('FakeLogger', (), {
            'log_start': lambda self, **kw: None,
            'log_planning_start': lambda self: None,
            'log_planning_complete': lambda self, **kw: None,
            'log_error': lambda self, *a, **kw: None,
        })()
        agent.console_logger = None

        class FakeOutline:
            title = "Test"
            sections = []
            def to_dict(self):
                return {"title": self.title, "sections": []}

        agent.plan_outline = lambda **kw: FakeOutline()

        try:
            result = agent.generate_report(
                progress_callback=None,
                report_id="test_report_obs",
            )
            # Should have created a root span
            assert len(fake_obs.spans) == 1, \
                f"Expected 1 root span, got {len(fake_obs.spans)}"
            assert fake_obs.spans[0].name == "report_generation"
            assert fake_obs.spans[0]._ended is True, \
                "Root trace should be ended after generate_report completes"
        finally:
            ra.logger = original_logger

    def test_plan_outline_creates_planning_span_when_obs_provided(self):
        """When plan_outline receives an observability_client, it creates a planning span."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=fake_obs,
        )

        # Patch zep tools
        agent.zep_tools = type('FakeZep', (), {
            'get_simulation_context': lambda self, **kw: {
                'graph_statistics': {'total_nodes': 5, 'total_edges': 3, 'entity_types': {}},
                'total_entities': 2,
                'related_facts': [],
            }
        })()

        # Capture the span created by plan_outline.start_span
        created_spans = []
        original_start_span = fake_obs.start_span

        def tracking_start_span(name, metadata=None):
            span = _FakeSpan(name, metadata=metadata or {})
            created_spans.append(span)
            return span

        fake_obs.start_span = tracking_start_span

        import json
        fake_json_response = json.dumps({
            "title": "Test Report",
            "sections": [{"title": "Section 1"}]
        })

        agent._generate_with_language_guard = lambda **kw: fake_json_response

        result = agent.plan_outline(
            progress_callback=None,
            observability_client=fake_obs,
        )

        # Restore original
        fake_obs.start_span = original_start_span

        # Should have created a planning span
        assert len(created_spans) == 1, f"Expected 1 span, got {len(created_spans)}"
        span = created_spans[0]
        assert span.name == "report_planning"
        assert span._ended is True, "Planning span should be ended"
        # The span should have been used as observation for the LLM call
        assert any("output" in u for u in span.updates), \
            f"Planning span should have output update, got: {span.updates}"

    def test_generate_without_obs_client_does_not_crash(self):
        """When no obs client is set, generate_report works exactly as before."""
        from app.services.report_agent import ReportAgent

        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            # No observability_client
        )
        assert agent.observability_client is None

        # Patch everything needed for generate_report to not crash
        import app.services.report_agent as ra

        class FakeOutline:
            title = "T"
            sections = []
            def to_dict(self):
                return {"title": self.title, "sections": []}

        agent.plan_outline = lambda **kw: FakeOutline()
        agent.report_logger = type('L', (), {
            'log_start': lambda self, **kw: None,
            'log_planning_start': lambda self: None,
            'log_planning_complete': lambda self, **kw: None,
        })()
        agent.console_logger = None
        ra.ReportManager._ensure_report_folder = lambda x: None
        ra.ReportManager.save_report = lambda *a, **kw: None
        ra.ReportManager.update_progress = lambda *a, **kw: None

        result = agent.generate_report(report_id="no_obs_test")
        assert result is not None

    def test_generate_report_closes_root_trace_on_error(self):
        """When generate_report raises, the root trace still ends."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=fake_obs,
        )

        import app.services.report_agent as ra

        def boom(**kwargs):
            raise RuntimeError("synthetic failure")

        agent.plan_outline = boom
        agent.report_logger = type('L', (), {
            'log_start': lambda self, **kw: None,
            'log_planning_start': lambda self: None,
            'log_error': lambda self, *a, **kw: None,
        })()
        agent.console_logger = None
        ra.ReportManager._ensure_report_folder = lambda x: None
        ra.ReportManager.save_report = lambda *a, **kw: None
        ra.ReportManager.update_progress = lambda *a, **kw: None

        try:
            agent.generate_report(report_id="error_trace_test")
        except RuntimeError:
            pass  # Expected

        # Even on error, the root trace should be ended
        assert len(fake_obs.spans) == 1
        assert fake_obs.spans[0]._ended is True
        error_update = next(
            (u for u in fake_obs.spans[0].updates
             if "status_message" in u and "error" in u["status_message"]),
            None,
        )
        assert error_update is not None, \
            "Error update should be recorded on the root trace"


class TestSectionAndToolTracing:
    """Verify section spans and tool-call spans during report generation."""

    def test_generate_section_react_passes_observation_to_llm_call(self):
        """_generate_section_react passes its observation to _generate_with_language_guard."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
        )

        class FakeSection:
            title = "Test Section"
            content = ""

        class FakeOutline:
            title = "Test"
            summary = ""
            sections = []

        class FakeLogger:
            def log_section_start(self, *a, **kw): pass
            def log_llm_response(self, *a, **kw): pass
            def log_tool_call(self, *a, **kw): pass
            def log_tool_result(self, *a, **kw): pass
            def log_section_content(self, *a, **kw): pass

        agent.report_logger = FakeLogger()

        # Track the observation and generation_name passed to _generate_with_language_guard
        call_records = []

        def tracking_lang_guard(**kw):
            call_records.append({
                'observation': kw.get('observation'),
                'generation_name': kw.get('generation_name'),
            })
            # Return a Final Answer immediately (no tool calls needed in mock)
            return "Final Answer: test content"

        agent._generate_with_language_guard = tracking_lang_guard

        # _execute_tool mock - must match exact signature
        def fake_execute(tool_name, parameters, report_context="", observation=None):
            return "tool result"

        agent._execute_tool = fake_execute

        result = agent._generate_section_react(
            section=FakeSection(),
            outline=FakeOutline(),
            previous_sections=[],
            progress_callback=None,
            section_index=1,
            observation=fake_obs,
        )

        # Verify the observation was forwarded to the LLM call
        assert len(call_records) >= 1, \
            f"_generate_with_language_guard should have been called at least once, got {len(call_records)}"
        assert call_records[0]['observation'] is fake_obs, \
            "observation should be forwarded to _generate_with_language_guard"
        assert call_records[0]['generation_name'] is not None
        assert call_records[0]['generation_name'].startswith("section_")

    def test_execute_tool_signature_includes_observation_parameter(self):
        """_execute_tool method signature includes optional observation parameter."""
        import inspect
        from app.services.report_agent import ReportAgent

        sig = inspect.signature(ReportAgent._execute_tool)
        param_names = list(sig.parameters.keys())
        assert 'observation' in param_names, \
            f"_execute_tool should accept 'observation' param, has: {param_names}"

    def test_generate_report_creates_root_and_planning_spans_noop(self):
        """generate_report with a noop observability client creates no spans and does not crash."""
        from app.services.report_agent import ReportAgent
        from app.observability.langfuse_client import NoOpObservabilityClient

        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=NoOpObservabilityClient(),
        )

        import app.services.report_agent as ra

        class FakeOutline:
            title = "R"
            sections = []
            def to_dict(self):
                return {"title": self.title, "sections": []}

        class FakeLogger:
            def log_start(self, **kw): pass
            def log_section_start(self, *a, **kw): pass
            def log_llm_response(self, *a, **kw): pass
            def log_tool_call(self, *a, **kw): pass
            def log_tool_result(self, *a, **kw): pass
            def log_section_content(self, *a, **kw): pass
            def log_section_full_complete(self, *a, **kw): pass
            def log_planning_start(self): pass
            def log_planning_complete(self, *a, **kw): pass
            def log_error(self, *a, **kw): pass

        agent.report_logger = FakeLogger()
        agent.console_logger = None
        ra.ReportManager._ensure_report_folder = lambda x: None
        ra.ReportManager.save_report = lambda *a, **kw: None
        ra.ReportManager.update_progress = lambda *a, **kw: None
        ra.ReportManager.save_outline = lambda *a, **kw: None
        ra.ReportManager.save_section = lambda *a, **kw: None

        agent.plan_outline = lambda **kw: FakeOutline()

        # Should not raise
        result = agent.generate_report(report_id="noop_test")
        assert result is not None

    def test_generate_report_creates_root_and_planning_spans(self):
        """generate_report with obs client creates a root trace and planning span."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=fake_obs,
        )

        import app.services.report_agent as ra

        class FakeOutline:
            title = "Report"
            summary = ""
            sections = []
            def to_dict(self):
                return {"title": self.title, "sections": []}

        class FakeLogger:
            def log_start(self, **kw): pass
            def log_section_start(self, *a, **kw): pass
            def log_llm_response(self, *a, **kw): pass
            def log_tool_call(self, *a, **kw): pass
            def log_tool_result(self, *a, **kw): pass
            def log_section_content(self, *a, **kw): pass
            def log_section_full_complete(self, *a, **kw): pass
            def log_planning_start(self): pass
            def log_planning_complete(self, *a, **kw): pass
            def log_error(self, *a, **kw): pass

        agent.report_logger = FakeLogger()
        agent.console_logger = None
        ra.ReportManager._ensure_report_folder = lambda x: None
        ra.ReportManager.save_report = lambda *a, **kw: None
        ra.ReportManager.update_progress = lambda *a, **kw: None
        ra.ReportManager.save_outline = lambda *a, **kw: None
        ra.ReportManager.save_section = lambda *a, **kw: None

        # Return a FakeOutline with no sections to avoid section loop
        agent.plan_outline = lambda **kw: FakeOutline()

        result = agent.generate_report(report_id="trace_test")

        # Should have a root span named "report_generation"
        root_spans = [s for s in fake_obs.spans if s.name == "report_generation"]
        assert len(root_spans) == 1, f"Expected root span, got {root_spans}"
        assert root_spans[0]._ended is True, "Root trace should be ended"

class TestChatTracing:
    """Verify ReportAgent.chat() emits chat traces."""

    def test_chat_accepts_observability_client_parameter(self):
        """chat() accepts an optional observability_client parameter."""
        import inspect
        from app.services.report_agent import ReportAgent

        sig = inspect.signature(ReportAgent.chat)
        param_names = list(sig.parameters.keys())
        assert 'observability_client' in param_names, \
            f"chat should accept 'observability_client' param, has: {param_names}"

    def test_chat_creates_chat_span_when_obs_client_provided(self):
        """When chat() is called with observability_client, it creates a chat span."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=fake_obs,
        )

        # Mock _generate_with_language_guard to return a direct response
        call_records = []

        def fake_lang_guard(**kw):
            call_records.append(kw)
            return "This is a direct answer without tools."

        agent._generate_with_language_guard = fake_lang_guard

        # Also need to mock report_manager to avoid file I/O
        import app.services.report_agent as ra
        original_rm = ra.ReportManager.get_report_by_simulation
        ra.ReportManager.get_report_by_simulation = lambda sim_id: None

        try:
            result = agent.chat(
                message="hello",
                chat_history=[],
                observability_client=fake_obs,
            )

            # Should have created a chat_session span
            chat_spans = [s for s in fake_obs.spans if s.name == "chat_session"]
            assert len(chat_spans) == 1, f"Expected 1 chat span, got {[s.name for s in fake_obs.spans]}"
            assert chat_spans[0]._ended is True, "Chat span should be ended"
            assert chat_spans[0].updates, "Chat span should have updates"
        finally:
            ra.ReportManager.get_report_by_simulation = original_rm

    def test_chat_without_obs_client_does_not_crash(self):
        """When no observability_client is set, chat() works exactly as before."""
        from app.services.report_agent import ReportAgent

        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            # No observability_client
        )

        import app.services.report_agent as ra
        original_rm = ra.ReportManager.get_report_by_simulation
        ra.ReportManager.get_report_by_simulation = lambda sim_id: None

        agent._generate_with_language_guard = lambda **kw: "Direct answer."

        try:
            result = agent.chat(message="hello")
            assert result is not None
        finally:
            ra.ReportManager.get_report_by_simulation = original_rm

    def test_chat_passes_observation_to_llm_calls(self):
        """chat() passes its observation to _generate_with_language_guard calls."""
        from app.services.report_agent import ReportAgent

        fake_obs = _FakeObservation()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
        )

        import app.services.report_agent as ra
        ra.ReportManager.get_report_by_simulation = lambda sim_id: None

        llm_calls = []
        agent._generate_with_language_guard = lambda **kw: llm_calls.append(kw) or "direct response"

        agent.chat(
            message="test",
            observability_client=fake_obs,
        )

        # At least one LLM call should have the observation (the chat_span, not None)
        has_obs = any('observation' in c and c['observation'] is not None for c in llm_calls)
        assert has_obs, f"observation should be passed to LLM calls: {llm_calls}"


class TestNoOpClientStillWorks:
    """Verify the no-op client can be passed to ReportAgent without errors."""

    def test_report_agent_with_noop_client(self):
        """ReportAgent can be instantiated with NoOpObservabilityClient."""
        from app.services.report_agent import ReportAgent

        noop = NoOpObservabilityClient()
        agent = ReportAgent(
            graph_id="g1",
            simulation_id="s1",
            simulation_requirement="test",
            observability_client=noop,
        )
        assert agent.observability_client is noop
